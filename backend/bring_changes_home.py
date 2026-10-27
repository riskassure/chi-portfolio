"""Conservatively refresh local databases from a verified live snapshot."""
from collections import Counter
from contextlib import closing, contextmanager
import hashlib
import json
from pathlib import Path
import sqlite3
import uuid

from download_live_database import verify
import diagram_home
import math_schema
import merge_sync
import photo_home

# File-backed content needs a separate download/reconciliation workflow.
FILE_TABLES = {'stg_spotify_import', 'photography_catalog',
               'music_publication', 'music_publication_meta',
               'google_photo_drafts', 'math_concept_diagrams', 'math_concept_diagram_failures'}
# Music catalog details and editorial overrides are database-only content. Compare
# their complete rows normally: live-only edits may come home, but divergent local
# edits must still block. They are not disposable regenerated Spotify rankings.
# Each website regenerates its own Spotify ranking on a timer and the ranking is
# never published from the laptop, so the live copy simply replaces the local one.
REGENERATED_TABLES = ('music_publication', 'music_publication_meta')
# Compared by content, with their SVGs synchronized, when refresh is given a diagrams folder.
DIAGRAM_TABLES = ('math_concept_diagrams', 'math_concept_diagram_failures')
# Math tables compared by what an entry is, not by row ids, timestamps or the generated page HTML,
# so a published entry matches the local one it came from.
MATH_TABLES = ('math_concepts', 'math_concept_classifications', 'math_concept_types', 'math_synonyms',
               'math_definitions', 'math_link_exclusions', 'math_related_concepts', 'math_concept_merges')
MATH_IGNORED = {'id', 'created_at', 'updated_at', 'rendered_tex', 'related_concept_id'}
# Columns holding an entry's id, compared as that entry's canonical name.
CONCEPT_COLUMNS = {'concept_id', 'retired_into_id', 'absorbed_id', 'survivor_id'}


def math_rows(db, name):
    """Return a math table's rows as content: concept ids become canonical names; ids and derived columns are dropped."""
    quoted = '"' + name.replace('"', '""') + '"'
    columns = [row[1] for row in db.execute('PRAGMA table_info(' + quoted + ')')]
    kept = [column for column in columns if column not in MATH_IGNORED]
    canonical = dict(db.execute('SELECT id, canonical_name FROM math_concepts'))
    rows = []
    for row in db.execute('SELECT ' + ','.join('"' + c.replace('"', '""') + '"' for c in kept) + ' FROM ' + quoted):
        rows.append(tuple((column, canonical.get(value, ('missing concept', value))
                           if column in CONCEPT_COLUMNS and value is not None else value)
                          for column, value in zip(kept, row)))
    return rows


def inventory(db, by_content=()):
    """Fingerprint every table. Tables in by_content (diagram and math tables) are compared by meaning."""
    if not db.in_transaction:
        db.execute('BEGIN')
    if db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok' or db.execute('PRAGMA foreign_key_check').fetchone():
        raise ValueError('Database integrity or foreign-key check failed.')
    schema = tuple(db.execute("SELECT type,name,tbl_name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name"))
    tables = {}
    for name, in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"):
        quoted = '"' + name.replace('"', '""') + '"'
        # Compare complete rows, including metadata omitted by the math preview.
        if name == 'math_concept_diagrams' and name in by_content:
            # Ids, block order and timestamps differ between a local render and the published row.
            tables[name] = Counter(hashlib.sha256(repr(row).encode('utf-8')).hexdigest()
                                   for row in diagram_home.rows(db))
        elif name == 'math_concept_diagram_failures' and name in by_content:
            tables[name] = Counter()  # Local render diagnostics; the new copies start without them.
        elif name in MATH_TABLES and name in by_content:
            tables[name] = Counter(hashlib.sha256(repr(row).encode('utf-8')).hexdigest() for row in math_rows(db, name))
        elif name == 'profile_page_revisions':
            columns = [row[1] for row in db.execute('PRAGMA table_info(' + quoted + ')') if row[1] != 'saved_at']
            projection = ','.join('"'+column.replace('"','""')+'"' for column in columns)
            rows = []
            for row in db.execute('SELECT ' + projection + ' FROM ' + quoted):
                values = list(row)
                if {'page', 'revision', 'content'} <= set(columns):
                    index = columns.index('content')
                    values[index] = json.dumps(json.loads(values[index]), sort_keys=True, ensure_ascii=False)
                rows.append(tuple(values))
            # Publishing appends the same revision at a different time. Preserve
            # comparison of all history and fields, but ignore save time/JSON spacing.
            tables[name] = Counter(hashlib.sha256(repr(row).encode('utf-8')).hexdigest() for row in rows)
        else:
            tables[name] = Counter(hashlib.sha256(repr(tuple(row)).encode('utf-8')).hexdigest()
                                   for row in db.execute('SELECT * FROM ' + quoted))
    return schema, tables


def assess(base, local, live, by_content=()):
    if base[0] != local[0] or base[0] != live[0]:
        return dict(safe=False, reason='Database schemas differ; review required.', blocked=[], live_changed=[])
    blocked = []
    changed = []
    for name in base[1]:
        if name in REGENERATED_TABLES:
            continue
        b, w, r = base[1][name], local[1][name], live[1][name]
        if w != b and w != r:
            blocked.append(name)
        if w != r:
            changed.append(name)
    assets = sorted(set(changed) & (FILE_TABLES - set(by_content)))
    return dict(safe=not blocked and not assets,
                reason=('Unpublished or divergent local rows need review.' if blocked else
                        'File-backed content changed; media synchronization needs review.' if assets else
                        'No unpublished local database rows would be lost.'),
                blocked=sorted(blocked), live_changed=sorted(changed), media_review=assets)


@contextmanager
def schema_upgraded_copies(baseline, local, live, folder, files, change_sets=()):
    """Return the three connections to compare, allowing for the known math schema upgrade and published merges.

    When live has the retirement schema upgrade and the baseline and working
    copy have none of it, the upgrade is applied to temporary copies of those
    two in folder. change_sets are merges, retirements or undos published
    since the last refresh (already confirmed against live): each is replayed
    onto the same copies, so the comparison sees them on all three sides and
    still catches every other local difference. files are the baseline and
    working database paths; they are copied through separate read-only
    connections because the refresh holds the working copy's write lock. The
    originals are never changed; the new copies are later made from live. In
    every other case return the connections as given, and a schema difference
    stops the refresh as before.
    """
    upgrade = (math_schema.state(live) == 'current' and math_schema.state(baseline) == 'absent'
               and math_schema.state(local) == 'absent')
    if not upgrade and not change_sets:
        yield baseline, local, live
        return
    paths = [folder / 'baseline-upgraded.db', folder / 'working-upgraded.db']
    copies = []
    try:
        for path, source in zip(paths, files):
            copy = sqlite3.connect(path)
            copies.append(copy)
            with closing(sqlite3.connect(Path(source).resolve().as_uri() + '?mode=ro', uri=True)) as reader:
                reader.backup(copy)
            copy.execute('BEGIN')
            if upgrade:
                math_schema.upgrade(copy)
            for change_set in change_sets:
                try:
                    merge_sync.replay(copy, change_set)
                except ValueError as error:
                    raise ValueError(f'The published {change_set["action"]} does not fit your local copy '
                                     f'({path.name}): {error} Saved paths and databases are unchanged.') from None
            copy.commit()
        yield copies[0], copies[1], live
    finally:
        for copy in copies:
            copy.close()
        for path in paths:
            path.unlink(missing_ok=True)


def published_change_sets(state, live):
    """The change sets of option 21 publishes awaiting this refresh, each confirmed against the live snapshot."""
    change_sets = [item['change_set'] for item in state.get('merge_pending_sync') or []]
    for change_set in change_sets:
        try:
            merge_sync.verify(live, change_set)
        except ValueError as error:
            raise ValueError(f'The published {change_set["action"]} of {change_set.get("absorbed") or change_set["merge"]["absorbed"]} '
                             f'does not match the live database: {error} Nothing was refreshed; review live first.') from None
    return change_sets


def refresh(state, snapshot, destination, save_state, frontend=None, diagrams=None):
    """Create new copies and switch saved paths only after a conservative comparison.

    With diagrams (the local diagrams folder), math and diagram rows are
    compared by content (ignoring row ids, timestamps and generated page
    HTML) and every SVG the live rows use is verified or downloaded.
    """
    snapshot = Path(snapshot).resolve()
    metadata = json.loads(snapshot.with_name('snapshot.json').read_text(encoding='utf-8'))
    if metadata.get('source') != f"/home/{state['username']}/chi-portfolio/backend/portfolio.db":
        raise ValueError('Snapshot belongs to a different account or database.')
    verify(snapshot, metadata['sha256'])
    base, working = Path(state['base']), Path(state['working'])
    if base.resolve() == working.resolve() or base.samefile(working):
        raise ValueError('Baseline and working database must be separate files.')
    if hashlib.sha256(base.read_bytes()).hexdigest() != state['base_sha256']:
        raise ValueError('Baseline changed; refresh stopped.')
    folder = Path(destination) / uuid.uuid4().hex
    folder.mkdir(parents=True, exist_ok=False)
    with closing(sqlite3.connect(base.resolve().as_uri()+'?mode=ro', uri=True)) as baseline, \
         closing(sqlite3.connect(working.resolve().as_uri()+'?mode=rw', uri=True, timeout=2)) as local, \
         closing(sqlite3.connect(snapshot.as_uri()+'?mode=ro', uri=True)) as live:
        # Prevent a local edit between comparison and switching the saved paths.
        # No SQL writes are issued, and closing rolls this transaction back.
        local.execute('BEGIN IMMEDIATE')
        by_content = DIAGRAM_TABLES + MATH_TABLES if diagrams is not None else ()
        change_sets = published_change_sets(state, live)
        with schema_upgraded_copies(baseline, local, live, folder, (base, working), change_sets) as compared:
            inventories = [inventory(db, by_content) for db in compared]
        photo_plan = None
        if frontend is not None:
            photo_plan = photo_home.reconcile(baseline, local, live)
            # The gallery has its own row comparison; local import drafts are
            # carried into the new working copy, never into the live baseline.
            inventories = [(tuple(row for row in schema if not
                            (row[0] == 'table' and row[1] == 'google_photo_drafts')),
                            {name: rows for name, rows in tables.items()
                             if name not in {'photography_catalog', 'google_photo_drafts'}})
                           for schema, tables in inventories]
        result = assess(*inventories, by_content=by_content)
        result['music_ranking_replaced'] = any(inventories[1][1].get(name) != inventories[2][1].get(name)
                                               for name in REGENERATED_TABLES)
        if photo_plan is not None:
            result['photo_conflicts'] = photo_plan['blocked']
            result['local_drafts_preserved'] = len(photo_plan['drafts'])
            if photo_plan['blocked']:
                result.update(safe=False, reason='Unpublished or divergent photos/drafts need review.')
        result.update(source=str(snapshot), previous_base=str(base), previous_working=str(working))
        report = folder/'comparison.json'
        report.write_text(json.dumps(dict(result, refresh_complete=False), indent=2), encoding='utf-8')
        if not result['safe']:
            return dict(result, report=str(folder/'comparison.json'))
        if photo_plan is not None:
            print('Verifying gallery images; downloading missing photos. Existing images will not be overwritten.', flush=True)
            manifest, staged = photo_home.stage_media(state['username'], photo_plan['paths'], frontend, folder)
        if diagrams is not None:
            print('Verifying math diagrams; downloading missing SVGs. Existing files will not be overwritten.', flush=True)
            diagram_manifest, diagram_staged, diagram_report = diagram_home.stage_media(
                state['username'], diagram_home.referenced(live), diagrams, folder)
        data = snapshot.read_bytes()
        if hashlib.sha256(data).hexdigest() != metadata['sha256']:
            raise ValueError('Snapshot changed during comparison.')
        for name in ('base.db', 'working.db'):
            with (folder/name).open('xb') as stream:
                stream.write(data)
            verify(folder/name, metadata['sha256'])
        if photo_plan is not None:
            with closing(sqlite3.connect(folder/'working.db')) as new_working:
                photo_home.preserve_drafts(new_working, photo_plan['drafts'])
                if new_working.execute('PRAGMA integrity_check').fetchone()[0] != 'ok' or new_working.execute('PRAGMA foreign_key_check').fetchone():
                    raise ValueError('New working database failed verification.')
            photo_home.install_media(frontend, manifest, staged)
            result.update(photos_verified=len(manifest), photos_downloaded=len(staged))
        if diagrams is not None:
            diagram_home.install_media(diagrams, diagram_manifest, diagram_staged)
            result.update(diagrams_verified=len(diagram_report['verified']), diagrams_downloaded=len(diagram_staged),
                          diagrams_kept_local=diagram_report['kept_local'],
                          diagrams_missing_on_server=diagram_report['missing_on_server'])
        (folder/'previous-workflow.json').write_text(json.dumps(state, indent=2), encoding='utf-8')
        updated = dict(state, base=str((folder/'base.db').resolve()),
                       working=str((folder/'working.db').resolve()),
                       base_sha256=metadata['sha256'], job=None, merge_pending_sync=[])
        save_state(updated)
        state.clear()
        state.update(updated)
        report.write_text(json.dumps(dict(result, refresh_complete=True), indent=2), encoding='utf-8')
    return dict(result, report=str(folder/'comparison.json'), working=state['working'])
