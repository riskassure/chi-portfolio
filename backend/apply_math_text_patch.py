"""Apply one reviewed change to an existing math entry (content and details). Run on the host from a private folder."""
import argparse
from contextlib import closing
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import sys
import uuid
from preview_math_sync import active_sql, read_snapshot, read_status
from publish_math_entry import media_fragments

LIST_FIELDS = ('classifications', 'types', 'synonyms', 'definitions', 'link_exclusions', 'related_concepts')
SNAPSHOT_FIELDS = {'slug', 'title', 'owner', 'cleaned_tex', 'is_cleaned', *LIST_FIELDS}


def check_stored_entry(expected):
    """Check only the shape of a stored entry; existing metadata is not held to new-entry rules."""
    if not isinstance(expected, dict) or set(expected) != SNAPSHOT_FIELDS:
        raise ValueError('Invalid expected entry.')
    for key in ('slug', 'title', 'owner', 'cleaned_tex'):
        if not isinstance(expected[key], str):
            raise ValueError('Invalid expected entry.')
    for key in LIST_FIELDS:
        if not isinstance(expected[key], list) or any(not isinstance(v, str) for v in expected[key]):
            raise ValueError('Invalid expected entry.')


# What an existing-entry patch may replace besides the content (replacement_tex),
# each as replacement_<field>. The slug is left out: it is the page's address,
# which other pages, search results and bookmarks use.
METADATA_FIELDS = ('title', 'owner', 'is_cleaned', *LIST_FIELDS)
REPLACEMENT_KEYS = {'replacement_' + key for key in METADATA_FIELDS}
# Every snapshot field an existing-entry patch can change.
PATCH_FIELDS = {'cleaned_tex', *METADATA_FIELDS}


def patch_payload(canonical, expected, proposed):
    """Return the patch that turns expected into proposed (both as read_snapshot gives them).

    Only metadata that differs is included, so the patch leaves the rest as stored.
    """
    payload = dict(canonical_name=canonical, expected=expected, replacement_tex=proposed['cleaned_tex'])
    payload.update({'replacement_' + key: proposed[key] for key in METADATA_FIELDS if proposed[key] != expected[key]})
    return payload


def _replacement(key, value):
    """Return a checked replacement value for one metadata field, or raise ValueError."""
    if key in ('title', 'owner'):
        if not isinstance(value, str) or not value.strip():
            raise ValueError('Missing text field: ' + key)
        if value != value.strip():
            raise ValueError(key.capitalize() + ' has leading or trailing spaces.')
        return value
    if key == 'is_cleaned':
        if type(value) is not int or value not in (0, 1):
            raise ValueError('Invalid cleaned flag.')
        return value
    if not isinstance(value, list) or any(not isinstance(v, str) or not v.strip() or v != v.strip()
                                          for v in value) or len(set(value)) != len(value):
        raise ValueError('Invalid metadata: ' + key)
    if key == 'synonyms' and len({s.casefold() for s in value}) != len(value):
        raise ValueError('Duplicate synonyms ignoring case.')
    if key in ('classifications', 'types') and not value:
        raise ValueError('Include classification and document type.')
    return sorted(value)


def patch_intended(payload):
    """Return the entry an existing-entry patch produces, or raise ValueError if it is unsafe.

    Only what the patch changes is validated, so an existing entry with missing
    classifications or duplicate unchanged metadata can still take a text fix.
    Diagrams and images must stay byte-identical (see media_fragments).
    """
    required = {'canonical_name', 'expected', 'replacement_tex'}
    if not isinstance(payload, dict) or not required <= payload.keys() or set(payload) - required - REPLACEMENT_KEYS:
        raise ValueError('Invalid existing-entry patch fields.')
    expected = payload['expected']
    check_stored_entry(expected)
    canonical, replacement = payload['canonical_name'], payload['replacement_tex']
    if not isinstance(canonical, str) or not canonical.strip():
        raise ValueError('Missing text field: canonical_name')
    if not isinstance(replacement, str) or not replacement.strip():
        raise ValueError('Missing text field: cleaned_tex')
    if media_fragments(replacement) != media_fragments(expected['cleaned_tex']):
        raise ValueError('Diagram or image changed: existing-entry patches must leave every diagram, '
                         'image and embed exactly as it is.')
    intended = dict(expected, cleaned_tex=replacement)
    for key in METADATA_FIELDS:
        if 'replacement_' + key in payload:
            intended[key] = _replacement(key, payload['replacement_' + key])
    if canonical in intended['related_concepts'] and intended['related_concepts'] != expected['related_concepts']:
        raise ValueError('An entry cannot be related to itself.')
    return intended


def detail_changes(expected, intended):
    """Return review lines for each metadata field that intended changes from expected."""
    lines = []
    for key in METADATA_FIELDS:
        before, after = expected[key], intended[key]
        if before == after:
            continue
        label = key.replace('_', ' ').capitalize()
        if key in LIST_FIELDS:
            lines += [label + ' added: ' + json.dumps(sorted(set(after) - set(before)), ensure_ascii=False),
                      label + ' removed: ' + json.dumps(sorted(set(before) - set(after)), ensure_ascii=False)]
        else:
            lines.append(label + ': ' + json.dumps(before, ensure_ascii=False) + ' -> ' + json.dumps(after, ensure_ascii=False))
    return lines


def metadata_conflict(db, canonical, expected, intended):
    """Return why the open database db cannot take intended's changed metadata, or None.

    The same rules as for a new entry, applied only to what changed: a new title
    must not be another active entry's title, synonym or defined term, and every
    added classification, type and related concept must exist (related ones active).
    """
    if intended['title'] != expected['title']:
        active = active_sql(db)
        if db.execute(f'SELECT 1 FROM math_concepts mc WHERE lower(trim(mc.title))=lower(trim(?)) '
                      f'AND mc.canonical_name<>? AND {active}', (intended['title'], canonical)).fetchone():
            return 'another entry already has the title ' + repr(intended['title'])
        for table, column in (('math_synonyms', 'synonym_text'), ('math_definitions', 'defined_term')):
            if db.execute(f'SELECT 1 FROM {table} a JOIN math_concepts mc ON mc.id=a.concept_id '
                          f'WHERE lower(trim(a.{column}))=lower(trim(?)) AND mc.canonical_name<>? AND {active}',
                          (intended['title'], canonical)).fetchone():
                return 'the new title ' + repr(intended['title']) + ' is a synonym or defined term of another entry'
    for key, table, column in (('classifications', 'math_classifications', 'code'),
                               ('types', 'math_types', 'type_name'),
                               ('related_concepts', 'math_concepts', 'canonical_name')):
        for value in sorted(set(intended[key]) - set(expected[key])):
            if not db.execute(f'SELECT 1 FROM {table} WHERE {column}=?', (value,)).fetchone():
                return 'no ' + key.replace('_', ' ').rstrip('s') + ' ' + repr(value) + ' exists on this database'
    added = sorted(set(intended['related_concepts']) - set(expected['related_concepts']))
    status = read_status(None, connection=db) if added else {}
    for value in added:
        if status[value]['retired']:
            survivor = status[value]['retired_into']
            return 'related concept ' + repr(value) + ' is retired' + (f'; relate to {survivor!r} instead' if survivor else '')
    return None


def metadata_conflict_in(database, canonical, expected, intended):
    """metadata_conflict against the database file at database, opened only when a checked field changed."""
    if all(intended[key] == expected[key] for key in ('title', 'classifications', 'types', 'related_concepts')):
        return None
    with closing(sqlite3.connect(Path(database).resolve().as_uri() + '?mode=ro', uri=True)) as db:
        return metadata_conflict(db, canonical, expected, intended)


def write_metadata(db, ident, expected, intended):
    """Store every metadata field where intended differs from expected, in the caller's transaction."""
    changed = [key for key in METADATA_FIELDS if intended[key] != expected[key]]
    for key in ('title', 'owner', 'is_cleaned'):
        if key in changed:
            db.execute(f'UPDATE math_concepts SET {key}=? WHERE id=?', (intended[key], ident))
    for key, table, fk, lookup, column in (('classifications', 'math_concept_classifications', 'classification_id',
                                            'math_classifications', 'code'),
                                           ('types', 'math_concept_types', 'type_id', 'math_types', 'type_name')):
        if key in changed:
            db.execute(f'DELETE FROM {table} WHERE concept_id=?', (ident,))
            for value in intended[key]:
                target = db.execute(f'SELECT id FROM {lookup} WHERE {column}=?', (value,)).fetchone()[0]
                db.execute(f'INSERT INTO {table}(concept_id,{fk}) VALUES(?,?)', (ident, target))
    for key, table, column in (('synonyms', 'math_synonyms', 'synonym_text'),
                               ('definitions', 'math_definitions', 'defined_term'),
                               ('link_exclusions', 'math_link_exclusions', 'word')):
        if key in changed:
            db.execute(f'DELETE FROM {table} WHERE concept_id=?', (ident,))
            db.executemany(f'INSERT INTO {table}(concept_id,{column}) VALUES(?,?)',
                           [(ident, value) for value in intended[key]])
    if 'related_concepts' in changed:
        db.execute('DELETE FROM math_related_concepts WHERE concept_id=?', (ident,))
        for value in intended['related_concepts']:
            target = db.execute('SELECT id FROM math_concepts WHERE canonical_name=?', (value,)).fetchone()[0]
            db.execute('INSERT INTO math_related_concepts(concept_id,related_canonical_name,related_concept_id) '
                       'VALUES(?,?,?)', (ident, value, target))


def missing_diagram_svgs(db, canonical, tex, extract_blocks):
    """Count PSTricks blocks in tex with no stored SVG for this entry.

    A text patch reuses stored SVGs and never runs LaTeX, so such a block would
    be published as a placeholder. extract_blocks is render_helper's extractor.
    """
    blocks = extract_blocks(tex)
    if not blocks:
        return 0
    try:
        stored = {row[0] for row in db.execute(
            'SELECT d.source_hash FROM math_concept_diagrams d JOIN math_concepts c ON c.id=d.concept_id '
            'WHERE c.canonical_name=? AND d.svg_path IS NOT NULL AND d.svg_path<>?', (canonical, ''))}
    except sqlite3.OperationalError:
        stored = set()
    return sum(block['source_hash'] not in stored for block in blocks)


def apply_patch(database, payload, backup_dir, source_dir):
    intended = patch_intended(payload)
    expected = payload['expected']
    replacement = payload['replacement_tex']
    canonical = payload['canonical_name']
    if not isinstance(replacement,str) or not replacement.strip():
        raise ValueError('Empty or invalid replacement.')
    sys.path.insert(0,str(source_dir))
    from services.math.render_helper import extract_all_pstricks_diagram_blocks
    from services.math.concept_render_service import render_tex_reusing_existing_diagrams
    # Compare sources, not whole block records: those carry offsets that move with any earlier text edit.
    if ([b['conversion_source'] for b in extract_all_pstricks_diagram_blocks(expected['cleaned_tex'])] !=
            [b['conversion_source'] for b in extract_all_pstricks_diagram_blocks(replacement)]):
        raise ValueError('Diagram changes are outside this text-only updater.')
    backup_dir.mkdir(parents=True,exist_ok=True)
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
    backup=backup_dir/('before-math-update-'+stamp+'.db')
    with closing(sqlite3.connect(database.resolve().as_uri()+'?mode=rw',uri=True,timeout=10)) as db:
        db.execute('BEGIN IMMEDIATE')
        current=read_snapshot(database,connection=db).get(canonical)
        if current != expected:
            raise ValueError('Conflict: live entry no longer matches the reviewed snapshot. Nothing changed.')
        if read_status(database, connection=db)[canonical]['retired']:
            raise ValueError('This entry is retired; undo the retirement before changing it. Nothing changed.')
        conflict=metadata_conflict(db,canonical,expected,intended)
        if conflict:
            raise ValueError('Conflict: '+conflict+'. Nothing changed.')
        missing=missing_diagram_svgs(db,canonical,replacement,extract_all_pstricks_diagram_blocks)
        if missing:
            raise ValueError(f'{missing} diagram(s) have no stored SVG and would show "[Diagram unavailable]". Nothing changed.')
        # The write lock prevents other writers between snapshot and update.
        with backup.open('xb'): pass
        with closing(sqlite3.connect(database.resolve().as_uri()+'?mode=ro',uri=True)) as src:
            with closing(sqlite3.connect(backup)) as dst:
                src.backup(dst)
                if dst.execute('PRAGMA integrity_check').fetchone()[0]!='ok':
                    raise ValueError('Backup failed integrity check.')
        ident=db.execute('SELECT id FROM math_concepts WHERE canonical_name=?',(canonical,)).fetchone()[0]
        rendered=render_tex_reusing_existing_diagrams(ident,replacement,db.cursor())
        db.execute('UPDATE math_concepts SET cleaned_tex=?, rendered_tex=?, updated_at=? WHERE id=?',
                   (replacement,rendered,datetime.now(timezone.utc).isoformat(),ident))
        write_metadata(db,ident,expected,intended)
        after=read_snapshot(database,connection=db)[canonical]
        if after != intended:
            raise ValueError('Verification failed. Update rolled back.')
        db.commit()
    print('Applied one existing-entry update:',canonical)
    print('Verified backup:',backup)
    return backup


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('patch',type=Path)
    parser.add_argument('--root',type=Path,default=Path.home()/'chi-portfolio')
    args=parser.parse_args()
    apply_patch(args.root/'backend/portfolio.db',json.loads(args.patch.read_text(encoding='utf-8')),
                args.root.parent/'backups',args.root/'backend/src')
