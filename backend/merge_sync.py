"""Merge, retire and undo math entries (helper option 21; design v3 sections 3, 5, 7 and 8).

A merge retires the absorbed entry A into the survivor S. A stays intact
apart from its three retirement columns; S gains copies of A's synonyms
(A's title included), defined terms, classifications and related links
that S lacks; entries already retired into A are repointed to S; the
math_concept_merges log records it all; and math_schema_meta records that
live now needs reader contract 1. A plain retirement only sets A's columns
and logs it. An undo reverses one of them while the recorded state holds.

Every publish computes a change set: the exact rows it changes, with
entries named by canonical name. replay() applies a change set, and both
the live publish and option 8 use it: option 8 confirms a published change
set against the live snapshot with verify() and replays it onto temporary
copies of the baseline and working database, so the comparison sees the
merge on all three sides and still catches every other local difference.
The log row holds the whole change set, so a publish found already applied
returns the same change set.

This module is sent to the server over SSH, so it uses only the standard
library and the helper modules sent with it.
"""
from contextlib import closing
from datetime import datetime, timezone
import difflib
import io
import json
from pathlib import Path
import re
import shlex
import shutil
import sqlite3
import subprocess
import uuid
import zipfile

import diagram_sync
import frontend_sync
import math_schema
from preview_math_sync import read_entry

KIND = 'math-merge'
VERSION = 1
# The reader contract a merge or retirement needs on live (see services/math/retirement.py).
CONTRACT = 1
ADDED = ('synonyms', 'definitions', 'classifications', 'related_concepts')
CONTRACT_PATH = ('services', 'math', 'retirement.py')
# A synonym may repeat another entry's defined term (synonyms win the autolink); nothing else may repeat.
ALLOWED_CLASH = ('synonym', 'definition')


class Conflict(ValueError):
    """Live content differs from what was reviewed."""


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


# ---------------------------------------------------------------- reading

def entry_state(db, canonical):
    """One entry as read_snapshot gives it, plus its stored diagrams (hash and source); None if missing."""
    entry = read_entry(db, canonical)
    if entry is not None:
        entry['diagrams'] = [dict(source_hash=row['source_hash'], source_tex=row['source_tex'])
                             for row in diagram_sync.stored_diagrams(db, canonical)]
    return entry


def ident(db, canonical):
    row = db.execute('SELECT id FROM math_concepts WHERE canonical_name = ?', (canonical,)).fetchone()
    if row is None:
        raise Conflict(f'There is no entry {canonical}.')
    return row[0]


def name_of(db, concept_id):
    row = db.execute('SELECT canonical_name FROM math_concepts WHERE id = ?', (concept_id,)).fetchone()
    return row[0] if row else None


def retirement(db, canonical):
    """{'retired_at', 'retired_into', 'reason'} for a retired entry (survivor by canonical name), else None."""
    row = db.execute('SELECT retired_at, retired_into_id, retirement_reason FROM math_concepts '
                     'WHERE canonical_name = ?', (canonical,)).fetchone()
    if row is None or row[0] is None:
        return None
    return dict(retired_at=row[0], retired_into=name_of(db, row[1]) if row[1] is not None else None, reason=row[2])


def retired_into(db, canonical):
    """Canonical names of the entries retired directly into canonical, sorted."""
    return sorted(row[0] for row in db.execute(
        'SELECT r.canonical_name FROM math_concepts r JOIN math_concepts t ON t.id = r.retired_into_id '
        'WHERE t.canonical_name = ? AND r.retired_at IS NOT NULL', (canonical,)))


def final_target(db, canonical, hops=5):
    """The active entry canonical leads to (itself, or its survivor); None if retired without one."""
    for _ in range(hops + 1):
        status = retirement(db, canonical)
        if status is None:
            return canonical if read_entry(db, canonical) is not None else None
        canonical = status['retired_into']
        if canonical is None:
            return None
    return None


def terms(entry, title_as='title'):
    """An entry's alias terms as (text, kind)."""
    return ([(entry['title'], title_as)] + [(t, 'synonym') for t in entry['synonyms']]
            + [(t, 'definition') for t in entry['definitions']])


def alias_clashes(db, owned, excluded):
    """Clashes of the (text, kind) terms with active entries other than the excluded canonical names.

    Each clash is {term, as, entry, their}: the term, the kind it has here,
    the other entry and the kind it has there. A synonym repeating another
    entry's defined term is allowed and not listed.
    """
    queries = {
        'title': 'SELECT canonical_name FROM math_concepts mc WHERE lower(trim(title)) = lower(trim(?))',
        'synonym': 'SELECT mc.canonical_name FROM math_synonyms s JOIN math_concepts mc ON mc.id = s.concept_id '
                   'WHERE lower(trim(s.synonym_text)) = lower(trim(?))',
        'definition': 'SELECT mc.canonical_name FROM math_definitions d JOIN math_concepts mc ON mc.id = d.concept_id '
                      'WHERE lower(trim(d.defined_term)) = lower(trim(?))',
    }
    found = set()
    for text, kind in owned:
        for their, query in queries.items():
            if (kind, their) == ALLOWED_CLASH:
                continue
            for name, in db.execute(query + ' AND mc.retired_at IS NULL', (text,)):
                if name not in excluded:
                    found.add((text, kind, name, their))
    return [dict(term=t, entry=n, their=r, **{'as': k}) for t, k, n, r in sorted(found)]


def clash_key(clash):
    return (clash['term'].strip().casefold(), clash['as'], clash['entry'], clash['their'])


def new_clashes(after, before):
    known = {clash_key(clash) for clash in before}
    return [clash for clash in after if clash_key(clash) not in known]


def describe_clashes(clashes):
    return '; '.join(f"{c['term']!r} ({c['as']}) is a {c['their']} of {c['entry']}" for c in clashes)


def incoming_links(db, canonical):
    """Active entries that link to canonical: by \\PMlinkname in their text, or as a related concept."""
    pattern = re.compile(r'\\PMlinkname\s*\{[^{}]*\}\s*\{\s*' + re.escape(canonical) + r'\s*\}')
    explicit = sorted(name for name, tex in db.execute(
        'SELECT canonical_name, cleaned_tex FROM math_concepts WHERE retired_at IS NULL AND canonical_name <> ?',
        (canonical,)) if tex and pattern.search(tex))
    related = sorted(row[0] for row in db.execute(
        'SELECT mc.canonical_name FROM math_related_concepts r JOIN math_concepts mc ON mc.id = r.concept_id '
        'WHERE r.related_canonical_name = ? AND mc.retired_at IS NULL AND mc.canonical_name <> ?',
        (canonical, canonical)))
    return dict(explicit=explicit, related=related)


# ---------------------------------------------------------------- payloads

FIELDS = {
    'merge': {'kind', 'version', 'action', 'session', 'absorbed', 'survivor', 'reason', 'keep_title',
              'metadata_only', 'absorbed_expected', 'survivor_before', 'survivor_after'},
    'retire': {'kind', 'version', 'action', 'session', 'absorbed', 'reason', 'absorbed_expected'},
    'undo': {'kind', 'version', 'action', 'undoes', 'change_set'},
}


def validate_payload(payload):
    if not isinstance(payload, dict) or payload.get('kind') != KIND or payload.get('version') != VERSION:
        raise ValueError('Invalid merge package.')
    action = payload.get('action')
    if action not in FIELDS or set(payload) != FIELDS[action]:
        raise ValueError('Invalid merge package fields.')
    if action == 'undo':
        change_set = payload['change_set']
        if (not isinstance(change_set, dict) or change_set.get('action') not in ('merge', 'retire')
                or change_set.get('package_sha256') != payload['undoes']
                or not re.fullmatch(r'[0-9a-f]{64}', payload['undoes'] or '')):
            raise ValueError('Invalid undo package.')
        return
    for key in ('absorbed', 'reason', 'session') + (('survivor',) if action == 'merge' else ()):
        if not isinstance(payload[key], str) or not payload[key].strip():
            raise ValueError('Missing ' + key + '.')
    entries = ('absorbed_expected',) + (('survivor_before', 'survivor_after') if action == 'merge' else ())
    if any(not isinstance(payload[key], dict) for key in entries):
        raise ValueError('Invalid entry snapshot in merge package.')
    if action == 'merge':
        if payload['absorbed'] == payload['survivor']:
            raise ValueError('An entry cannot be merged into itself.')
        if type(payload['keep_title']) is not bool or type(payload['metadata_only']) is not bool:
            raise ValueError('Invalid merge options.')


def title_of(payload):
    if payload['action'] == 'undo':
        change_set = payload['change_set']
        return ('Undo merge of ' + change_set['absorbed'] + ' into ' + change_set['survivor']
                if change_set['action'] == 'merge' else 'Undo retirement of ' + change_set['absorbed'])
    if payload['action'] == 'merge':
        return 'Merge ' + payload['absorbed'] + ' into ' + payload['survivor']
    return 'Retire ' + payload['absorbed']


def review(payload):
    """Describe the package from its content alone; the rows are computed again on live under lock."""
    validate_payload(payload)
    lines = ['Proposed operation: ' + title_of(payload)]
    if payload['action'] == 'undo':
        change_set = payload['change_set']
        lines += [f"Reverses the {change_set['action']} published at {change_set['at']} "
                  f"(package {change_set['package_sha256']}).",
                  f"{change_set['absorbed']} becomes active again; its own content was never changed."]
        for key in ADDED:
            if change_set['added'][key]:
                lines.append(f"Removed from {change_set['survivor']}, {key}: " + json.dumps(change_set['added'][key]))
        if change_set['repointed']:
            lines.append('Redirects put back to ' + change_set['absorbed'] + ': ' + ', '.join(change_set['repointed']))
        lines.append("The survivor's text is not changed; restoring it is a separate text publish (options 2-5).")
        return '\n'.join(lines)
    absorbed = payload['absorbed_expected']
    lines += ['Reason: ' + payload['reason'],
              f"{payload['absorbed']} ({absorbed['title']}, /{absorbed['slug']}) is retired, not deleted: "
              'its row and metadata stay as they are, its name and URL stay reserved.']
    if payload['action'] == 'retire':
        lines += ['No survivor: its old URL shows a retirement notice; links to it show as plain text.',
                  'No rows are added anywhere.']
        return '\n'.join(lines)
    before, after = payload['survivor_before'], payload['survivor_after']
    lines += [f"Its old URL and links to it lead to {payload['survivor']} ({after['title']}, /{after['slug']}).",
              f"Copied to {payload['survivor']} where it lacks them (checked again on live):",
              '  title as a synonym: ' + ('yes' if payload['keep_title'] else 'no'),
              '  synonyms: ' + json.dumps(absorbed['synonyms']),
              '  defined terms: ' + json.dumps(absorbed['definitions']),
              '  classifications: ' + json.dumps(absorbed['classifications']),
              '  related links: ' + json.dumps(absorbed['related_concepts']),
              'Entries already retired into it are repointed to the survivor.',
              f"Required on live: {payload['survivor']} exactly as approved below (text, metadata and diagrams), "
              f"published beforehand with options 2-5, and {payload['absorbed']} unchanged since the session started.",
              'Survivor text, frozen at the session start -> as approved:']
    lines += list(difflib.unified_diff(before['cleaned_tex'].splitlines(), after['cleaned_tex'].splitlines(),
                                       fromfile='survivor before', tofile='survivor approved', lineterm='')) or [
        '  (unchanged: metadata-only merge)']
    return '\n'.join(lines)


def write_package(path, payload):
    validate_payload(payload)
    with zipfile.ZipFile(path, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(KIND + '.json', json.dumps(payload, indent=2, ensure_ascii=False))


# ---------------------------------------------------------------- change sets

def log_fields(change_set):
    """The math_concept_merges.added_rows_json of a merge or retirement change set."""
    return json.dumps({key: change_set[key] for key in ('action', 'added', 'repointed', 'alias_clashes_before',
                                                         'alias_warnings')}, sort_keys=True, ensure_ascii=False)


def change_set_from_log(db, row_id):
    """Rebuild the change set a merge or retirement stored in its log row."""
    row = db.execute('SELECT absorbed_id, survivor_id, applied_at, reason, survivor_before_json, survivor_after_json, '
                     'added_rows_json, package_sha256 FROM math_concept_merges WHERE id = ?', (row_id,)).fetchone()
    stored = json.loads(row[6])
    return dict(stored, absorbed=name_of(db, row[0]), survivor=name_of(db, row[1]) if row[1] is not None else None,
                at=row[2], reason=row[3], survivor_before_json=row[4], survivor_after_json=row[5],
                package_sha256=row[7])


def log_row(db, package_sha256):
    """(id, undone_at) of the log row a package wrote, or None."""
    return db.execute('SELECT id, undone_at FROM math_concept_merges WHERE package_sha256 = ?',
                      (package_sha256,)).fetchone()


def plan(db, payload, package_sha256, at):
    """Compute the change set of a merge or plain retirement on db as it is now; never writes."""
    absorbed, survivor = payload['absorbed'], payload.get('survivor')
    a = entry_state(db, absorbed)
    before = alias_clashes(db, terms(a), {absorbed})
    change_set = dict(action=payload['action'], absorbed=absorbed, survivor=survivor, at=at,
                      reason=payload['reason'], package_sha256=package_sha256, repointed=retired_into(db, absorbed),
                      added={key: [] for key in ADDED}, alias_clashes_before=before, alias_warnings=[],
                      survivor_before_json=None, survivor_after_json=None)
    if payload['action'] == 'retire':
        if change_set['repointed']:
            raise ValueError('These entries are retired into ' + absorbed + ' and would lose their redirect: '
                             + ', '.join(change_set['repointed']) + '. Merge it into a survivor instead.')
        return change_set
    s = entry_state(db, survivor)
    added = change_set['added']
    seen = {t.strip().casefold() for t in [s['title']] + s['synonyms'] + s['definitions']}
    for value, key in ([(a['title'], 'synonyms')] if payload['keep_title'] else []) + \
            [(t, 'synonyms') for t in a['synonyms']] + [(t, 'definitions') for t in a['definitions']]:
        if value.strip().casefold() not in seen:
            seen.add(value.strip().casefold())
            added[key].append(value)
    added['classifications'] = sorted(set(a['classifications']) - set(s['classifications']))
    for name in a['related_concepts']:
        target = final_target(db, name)
        if target not in (None, survivor, absorbed) and target not in s['related_concepts'] \
                and target not in added['related_concepts']:
            added['related_concepts'].append(target)
    owned = [(t, 'synonym') for t in added['synonyms']] + [(t, 'definition') for t in added['definitions']]
    after = alias_clashes(db, owned, {absorbed, survivor})
    fresh = new_clashes(after, before)
    if fresh:
        raise ValueError('The merge would create alias clashes: ' + describe_clashes(fresh))
    change_set.update(alias_warnings=after,
                      survivor_before_json=json.dumps(payload['survivor_before'], sort_keys=True, ensure_ascii=False),
                      survivor_after_json=json.dumps(payload['survivor_after'], sort_keys=True, ensure_ascii=False))
    return change_set


ROW_TABLES = {
    'synonyms': ('math_synonyms', 'synonym_text'),
    'definitions': ('math_definitions', 'defined_term'),
}


def _add_rows(db, survivor_id, added):
    for key, (table, column) in ROW_TABLES.items():
        db.executemany(f'INSERT INTO {table}(concept_id, {column}) VALUES (?, ?)',
                       [(survivor_id, value) for value in added[key]])
    for code in added['classifications']:
        row = db.execute('SELECT id FROM math_classifications WHERE code = ?', (code,)).fetchone()
        if row is None:
            raise Conflict('Missing classification ' + code + '.')
        db.execute('INSERT INTO math_concept_classifications(concept_id, classification_id) VALUES (?, ?)',
                   (survivor_id, row[0]))
    for name in added['related_concepts']:
        db.execute('INSERT INTO math_related_concepts(concept_id, related_canonical_name, related_concept_id) '
                   'VALUES (?, ?, ?)', (survivor_id, name, ident(db, name)))


def _remove_rows(db, survivor_id, added):
    """Delete exactly one row for each added value, or raise if any is gone."""
    statements = [(f'SELECT rowid FROM {table} WHERE concept_id = ? AND {column} = ?', table, value)
                  for key, (table, column) in ROW_TABLES.items() for value in added[key]]
    statements += [('SELECT m.rowid FROM math_concept_classifications m JOIN math_classifications c '
                    'ON c.id = m.classification_id WHERE m.concept_id = ? AND c.code = ?',
                    'math_concept_classifications', code) for code in added['classifications']]
    statements += [('SELECT rowid FROM math_related_concepts WHERE concept_id = ? AND related_canonical_name = ?',
                    'math_related_concepts', name) for name in added['related_concepts']]
    for query, table, value in statements:
        row = db.execute(query + ' LIMIT 1', (survivor_id, value)).fetchone()
        if row is None:
            raise Conflict(f'A row the merge added is gone: {value!r} in {table}.')
        db.execute(f'DELETE FROM {table} WHERE rowid = ?', (row[0],))


def _require_active(db, canonical):
    status = retirement(db, canonical)
    if status is not None:
        raise Conflict(f'{canonical} is retired' + (f" into {status['retired_into']}." if status['retired_into'] else '.'))
    return ident(db, canonical)


def replay(db, change_set):
    """Apply one change set inside the caller's transaction; raise, changing nothing it commits, if it does not fit."""
    if change_set['action'] == 'undo':
        return _replay_undo(db, change_set)
    absorbed_id = _require_active(db, change_set['absorbed'])
    survivor_id = _require_active(db, change_set['survivor']) if change_set['survivor'] else None
    if log_row(db, change_set['package_sha256']):
        raise Conflict('This package is already recorded.')
    if survivor_id is not None:
        _add_rows(db, survivor_id, change_set['added'])
    for name in change_set['repointed']:
        if retirement(db, name) is None or retirement(db, name)['retired_into'] != change_set['absorbed']:
            raise Conflict(f"{name} is no longer retired into {change_set['absorbed']}.")
        db.execute('UPDATE math_concepts SET retired_into_id = ? WHERE id = ?', (survivor_id, ident(db, name)))
    db.execute('UPDATE math_concepts SET retired_at = ?, retired_into_id = ?, retirement_reason = ? WHERE id = ?',
               (change_set['at'], survivor_id, change_set['reason'], absorbed_id))
    db.execute('INSERT INTO math_concept_merges(absorbed_id, survivor_id, applied_at, undone_at, reason, '
               'survivor_before_json, survivor_after_json, added_rows_json, package_sha256) '
               'VALUES (?, ?, ?, NULL, ?, ?, ?, ?, ?)',
               (absorbed_id, survivor_id, change_set['at'], change_set['reason'], change_set['survivor_before_json'],
                change_set['survivor_after_json'], log_fields(change_set), change_set['package_sha256']))
    if math_schema.required_contract(db) < CONTRACT:
        db.execute('UPDATE math_schema_meta SET value = ? WHERE key = ?', (str(CONTRACT), math_schema.CONTRACT_KEY))


def _replay_undo(db, change_set):
    merged = change_set['merge']
    absorbed, survivor = merged['absorbed'], merged['survivor']
    row = log_row(db, merged['package_sha256'])
    if row is None or row[1] is not None:
        raise Conflict('The ' + merged['action'] + ' to undo is not recorded as active.')
    status = retirement(db, absorbed)
    if status != dict(retired_at=merged['at'], retired_into=survivor, reason=merged['reason']):
        raise Conflict(f'{absorbed} is no longer retired as recorded.')
    if survivor is not None:
        survivor_id = _require_active(db, survivor)
        _remove_rows(db, survivor_id, merged['added'])
        for name in merged['repointed']:
            if retirement(db, name) is None or retirement(db, name)['retired_into'] != survivor:
                raise Conflict(f'{name} no longer redirects to {survivor}.')
            db.execute('UPDATE math_concepts SET retired_into_id = ? WHERE id = ?',
                       (ident(db, absorbed), ident(db, name)))
    db.execute('UPDATE math_concepts SET retired_at = NULL, retired_into_id = NULL, retirement_reason = NULL '
               'WHERE id = ?', (ident(db, absorbed),))
    db.execute('UPDATE math_concept_merges SET undone_at = ? WHERE id = ?', (change_set['at'], row[0]))


def verify(db, change_set):
    """Raise Conflict unless db holds exactly what change_set records; never writes.

    Used after a publish, and by option 8 to confirm a receipt against the live snapshot.
    """
    if change_set['action'] == 'undo':
        merged = change_set['merge']
        row = log_row(db, merged['package_sha256'])
        if row is None or row[1] != change_set['at']:
            raise Conflict('The undo is not recorded on live as in the receipt.')
        if change_set_from_log(db, row[0]) != merged:
            raise Conflict('The undone log record differs from the receipt.')
        if retirement(db, merged['absorbed']) is not None:
            raise Conflict(f"{merged['absorbed']} is still retired.")
        if merged['survivor'] is not None:
            s = entry_state(db, merged['survivor'])
            for key in ('synonyms', 'definitions', 'related_concepts', 'classifications'):
                if set(merged['added'][key]) & set(s[key]):
                    raise Conflict(f"{merged['survivor']} still has {key} the merge added.")
            for name in merged['repointed']:
                if (retirement(db, name) or {}).get('retired_into') != merged['absorbed']:
                    raise Conflict(f"{name} does not redirect to {merged['absorbed']} again.")
        return
    row = log_row(db, change_set['package_sha256'])
    if row is None or row[1] is not None:
        raise Conflict('The ' + change_set['action'] + ' is not recorded on live as in the receipt.')
    if change_set_from_log(db, row[0]) != change_set:
        raise Conflict('The log record on live differs from the receipt.')
    if retirement(db, change_set['absorbed']) != dict(retired_at=change_set['at'], retired_into=change_set['survivor'],
                                                       reason=change_set['reason']):
        raise Conflict(f"{change_set['absorbed']} is not retired as recorded.")
    if change_set['survivor'] is not None:
        s = entry_state(db, change_set['survivor'])
        if s is None or retirement(db, change_set['survivor']) is not None:
            raise Conflict(f"{change_set['survivor']} is not active.")
        for key in ADDED:
            missing = set(change_set['added'][key]) - set(s[key])
            if missing:
                raise Conflict(f"{change_set['survivor']} lacks {key} the merge added: {sorted(missing)}")
        for name in change_set['repointed']:
            if (retirement(db, name) or {}).get('retired_into') != change_set['survivor']:
                raise Conflict(f"{name} does not redirect to {change_set['survivor']}.")
    if math_schema.required_contract(db) < CONTRACT:
        raise Conflict('The live database does not record retirement contract ' + str(CONTRACT) + '.')


# ---------------------------------------------------------------- checks and publishing

def code_contract(source_dir):
    """The RETIREMENT_CONTRACT the website code in source_dir declares, or None."""
    path = Path(source_dir).joinpath(*CONTRACT_PATH)
    return frontend_sync.declared_contract(path.read_text(encoding='utf-8')) if path.is_file() else None


def already(db, payload, package_sha256):
    """The change set if this package is already applied, else None."""
    if payload['action'] == 'undo':
        row = log_row(db, payload['undoes'])
        if row is None or row[1] is None:
            return None
        return dict(action='undo', at=row[1], merge=change_set_from_log(db, row[0]),
                    package_sha256=package_sha256, undoes=payload['undoes'])
    row = log_row(db, package_sha256)
    return change_set_from_log(db, row[0]) if row else None


def check_and_apply(db, payload, package_sha256, source_dir, at):
    """Every check, then the change, then verification, inside the caller's transaction; return the change set.

    Raises Conflict when live differs from what was reviewed, ValueError when
    the operation is not allowed. source_dir None skips the deployed-code check
    (used for local previews only).
    """
    validate_payload(payload)
    if math_schema.state(db) != 'current':
        raise ValueError('The live database does not have the retirement schema upgrade (option 21, 1).')
    if source_dir is not None and (code_contract(source_dir) or 0) < CONTRACT:
        raise ValueError(f'The live website code does not declare retirement contract {CONTRACT}; '
                         'publish the retirement-aware code with option 15 first.')
    if payload['action'] == 'undo':
        return _check_and_undo(db, payload, package_sha256, at)
    absorbed = payload['absorbed']
    _require_active(db, absorbed)
    if entry_state(db, absorbed) != payload['absorbed_expected']:
        raise Conflict(f'{absorbed} changed on live since the session started. Start a new session.')
    if payload['action'] == 'merge':
        survivor = payload['survivor']
        _require_active(db, survivor)
        if entry_state(db, survivor) != payload['survivor_after']:
            raise Conflict(f'{survivor} on live is not the approved version. Publish it with options 2-5 first, '
                           'or prepare the merge again.')
        if payload['survivor_after'] == payload['survivor_before'] and not payload['metadata_only']:
            raise ValueError('The survivor is unchanged since the session started; confirm a metadata-only merge.')
    change_set = plan(db, payload, package_sha256, at)
    replay(db, change_set)
    verify(db, change_set)
    return change_set


def _check_and_undo(db, payload, package_sha256, at):
    merged = payload['change_set']
    row = log_row(db, payload['undoes'])
    if row is None:
        raise Conflict('The ' + merged['action'] + ' to undo is not recorded on live.')
    if change_set_from_log(db, row[0]) != merged:
        raise Conflict('The log record on live differs from the saved receipt.')
    absorbed, survivor = merged['absorbed'], merged['survivor']
    later = db.execute('SELECT a.canonical_name FROM math_concept_merges m JOIN math_concepts a ON a.id = m.absorbed_id '
                       'LEFT JOIN math_concepts s ON s.id = m.survivor_id WHERE m.id > ? AND m.undone_at IS NULL '
                       'AND (a.canonical_name IN (?, ?) OR s.canonical_name IN (?, ?))',
                       (row[0], absorbed, survivor, absorbed, survivor)).fetchall()
    if later:
        raise ValueError('Undo the later merge or retirement of ' + ', '.join(sorted(r[0] for r in later)) + ' first.')
    if survivor is None and retired_into(db, absorbed):
        raise ValueError('These entries have since been retired into ' + absorbed + ': '
                         + ', '.join(retired_into(db, absorbed)) + '. Undo those first.')
    change_set = dict(action='undo', at=at, merge=merged, package_sha256=package_sha256, undoes=payload['undoes'])
    replay(db, change_set)
    # A is active again: its aliases must not clash with anything that became active meanwhile.
    fresh = new_clashes(alias_clashes(db, terms(entry_state(db, absorbed)), {absorbed}), merged['alias_clashes_before'])
    if fresh:
        raise ValueError('Undo would create alias clashes: ' + describe_clashes(fresh))
    verify(db, change_set)
    return change_set


def summary(change_set):
    if change_set['action'] == 'undo':
        return 'undoes the ' + change_set['merge']['action'] + ' of ' + change_set['merge']['absorbed']
    counts = ', '.join(f"{len(v)} {k}" for k, v in change_set['added'].items() if v)
    text = (f"retires {change_set['absorbed']}" + (f" into {change_set['survivor']}" if change_set['survivor'] else '')
            + (f'; adds {counts}' if counts else '')
            + (f"; repoints {', '.join(change_set['repointed'])}" if change_set['repointed'] else ''))
    if change_set['alias_warnings']:
        text += '; existing alias overlaps kept: ' + describe_clashes(change_set['alias_warnings'])
    return text


def status(database, payload, package_sha256, source_dir=None, connection=None):
    """One-line verdict, from a private in-memory copy of database; never writes to it."""
    work = sqlite3.connect(':memory:')
    with (closing(sqlite3.connect(Path(database).resolve().as_uri() + '?mode=ro', uri=True))
          if connection is None else math_schema._borrowed(connection)) as source:
        source.backup(work)
    try:
        existing = already(work, payload, package_sha256)
        if existing is not None:
            return 'ALREADY PRESENT — ' + summary(existing)
        work.execute('BEGIN')
        return 'ELIGIBLE — ' + summary(check_and_apply(work, payload, package_sha256, source_dir, now()))
    except Conflict as error:
        return 'CONFLICT — ' + str(error)
    except ValueError as error:
        return 'BLOCKED — ' + str(error)
    finally:
        work.close()


def apply(database, payload, backup_dir, source_dir, package_sha256):
    """Publish: under one write lock, check, back up, change, verify and commit. Return the receipt fields."""
    validate_payload(payload)
    with closing(sqlite3.connect(Path(database).resolve().as_uri() + '?mode=rw', uri=True, timeout=10)) as db:
        db.execute('PRAGMA foreign_keys=ON')
        db.execute('BEGIN IMMEDIATE')
        existing = already(db, payload, package_sha256)
        if existing is not None:
            return dict(status='ALREADY_PRESENT', canonical=title_of(payload), backup=None, change_set=existing)
        backup = Path(backup_dir) / ('before-math-merge-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
                                     + '-' + uuid.uuid4().hex[:8] + '.db')
        backup.parent.mkdir(parents=True, exist_ok=True)
        with backup.open('xb'):
            pass
        # The write lock held above keeps the database unchanged while it is copied.
        with closing(sqlite3.connect(Path(database).resolve().as_uri() + '?mode=ro', uri=True)) as source, \
                closing(sqlite3.connect(backup)) as destination:
            source.backup(destination)
            if destination.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                raise ValueError('Backup failed integrity check.')
        change_set = check_and_apply(db, payload, package_sha256, source_dir, now())
        if db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok' or db.execute('PRAGMA foreign_key_check').fetchone():
            raise ValueError('Database check failed after the change; rolled back.')
        db.commit()
    return dict(status='APPLIED', canonical=title_of(payload), backup=str(backup), change_set=change_set)


def unpack(data):
    """The payload of a merge package (bytes)."""
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        if archive.namelist() != [KIND + '.json']:
            raise ValueError('Invalid merge package.')
        payload = json.loads(archive.read(KIND + '.json'))
    validate_payload(payload)
    return payload


# ---------------------------------------------------------------- reading live (option 21 sessions)

def view(database, canonicals, source_dir):
    """What a merge session needs from live, read-only: schema, contracts and the named entries."""
    with closing(sqlite3.connect(Path(database).resolve().as_uri() + '?mode=ro', uri=True)) as db:
        db.row_factory = sqlite3.Row
        db.execute('BEGIN')
        schema = math_schema.state(db)
        entries = {}
        for canonical in canonicals:
            entries[canonical] = dict(entry=entry_state(db, canonical),
                                      retirement=retirement(db, canonical) if schema == 'current' else None,
                                      retired_into=retired_into(db, canonical) if schema == 'current' else [])
        return dict(schema=schema, contract_required=math_schema.required_contract(db),
                    code_contract=code_contract(source_dir), entries=entries)


# The helper modules view() needs, in load order. Only these local, reviewed modules are sent.
VIEW_MODULES = ('preview_math_sync', 'diagram_sync', 'frontend_sync', 'math_schema', 'merge_sync')
VIEW_BOOTSTRAP = '''
import sys, json, types
from pathlib import Path
config = json.load(sys.stdin)
for name, source in config['modules']:
    module = types.ModuleType(name)
    module.__file__ = '<trusted-local-merge-view>/' + name + '.py'
    sys.modules[name] = module
    exec(compile(source, module.__file__, 'exec'), module.__dict__)
from merge_sync import view
database = Path(config['database'])
print('MERGE_VIEW_RESULT=' + json.dumps(view(database, config['canonicals'], database.parent / 'src')))
'''


def live_view(username, canonicals):
    """Read view() from the live site over SSH, without changing anything."""
    if not re.fullmatch(r'[A-Za-z0-9_]+', username):
        raise ValueError('Invalid username.')
    if not shutil.which('ssh'):
        raise ValueError('Windows OpenSSH Client is required.')
    request = dict(database=f'/home/{username}/chi-portfolio/backend/portfolio.db', canonicals=list(canonicals),
                   modules=[(name, Path(__file__).with_name(name + '.py').read_text(encoding='utf-8'))
                            for name in VIEW_MODULES])
    print('Reading the two entries from live, read-only. SSH may ask for your PythonAnywhere password.', flush=True)
    result = subprocess.run(['ssh', username + '@ssh.pythonanywhere.com',
                             'python3.13 -I -B -c ' + shlex.quote(VIEW_BOOTSTRAP)],
                            input=json.dumps(request), stdout=subprocess.PIPE, text=True, encoding='utf-8', check=True)
    lines = [line[len('MERGE_VIEW_RESULT='):] for line in result.stdout.splitlines()
             if line.startswith('MERGE_VIEW_RESULT=')]
    if len(lines) != 1:
        raise ValueError('No unambiguous reading of live received; nothing prepared.')
    return json.loads(lines[0])
