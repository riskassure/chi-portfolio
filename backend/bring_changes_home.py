"""Conservatively refresh local databases from a verified live snapshot."""
from collections import Counter
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import uuid

from download_live_database import verify

# File-backed content needs a separate download/reconciliation workflow.
FILE_TABLES = {'music_catalog', 'stg_spotify_import', 'photography_catalog',
               'music_publication', 'music_publication_meta', 'music_overrides',
               'google_photo_drafts', 'math_concept_diagrams', 'math_concept_diagram_failures'}


def inventory(db):
    if not db.in_transaction:
        db.execute('BEGIN')
    if db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok' or db.execute('PRAGMA foreign_key_check').fetchone():
        raise ValueError('Database integrity or foreign-key check failed.')
    schema = tuple(db.execute("SELECT type,name,tbl_name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name"))
    tables = {}
    for name, in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"):
        quoted = '"' + name.replace('"', '""') + '"'
        # Compare complete rows, including metadata omitted by the math preview.
        if name == 'profile_page_revisions':
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


def assess(base, local, live):
    if base[0] != local[0] or base[0] != live[0]:
        return dict(safe=False, reason='Database schemas differ; review required.', blocked=[], live_changed=[])
    blocked = []
    changed = []
    for name in base[1]:
        b, w, r = base[1][name], local[1][name], live[1][name]
        if w != b and w != r:
            blocked.append(name)
        if w != r:
            changed.append(name)
    assets = sorted(set(changed) & FILE_TABLES)
    return dict(safe=not blocked and not assets,
                reason=('Unpublished or divergent local rows need review.' if blocked else
                        'File-backed content changed; media synchronization needs review.' if assets else
                        'No unpublished local database rows would be lost.'),
                blocked=sorted(blocked), live_changed=sorted(changed), media_review=assets)


def refresh(state, snapshot, destination, save_state):
    """Create new copies and switch saved paths only after a conservative comparison."""
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
        result = assess(inventory(baseline), inventory(local), inventory(live))
        result.update(source=str(snapshot), previous_base=str(base), previous_working=str(working))
        (folder/'comparison.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
        if not result['safe']:
            return dict(result, report=str(folder/'comparison.json'))
        data = snapshot.read_bytes()
        if hashlib.sha256(data).hexdigest() != metadata['sha256']:
            raise ValueError('Snapshot changed during comparison.')
        for name in ('base.db', 'working.db'):
            with (folder/name).open('xb') as stream:
                stream.write(data)
            verify(folder/name, metadata['sha256'])
        (folder/'previous-workflow.json').write_text(json.dumps(state, indent=2), encoding='utf-8')
        updated = dict(state, base=str((folder/'base.db').resolve()),
                       working=str((folder/'working.db').resolve()),
                       base_sha256=metadata['sha256'], job=None)
        save_state(updated)
        state.clear()
        state.update(updated)
    return dict(result, report=str(folder/'comparison.json'), working=state['working'])
