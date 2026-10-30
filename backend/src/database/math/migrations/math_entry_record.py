"""Replay batches of new math entries published with helper option 20.

Shared by the add_<topic>_entries_<date>.py migrations that helper option 23
writes (or --write below). Each lists the batch's entries as the payloads of
the packages you reviewed, in the order option 20 published them, which is the
order of their ids on live. replay() rebuilds each package and applies it with
live_math_publication.publish, the code the live site ran, so its checks
(duplicates, missing related entries, the full-match test) are the live ones.
An entry already present with the same content is skipped, so a migration can
run again; anything that conflicts stops.

Diagram SVGs are kept in git beside the migration, in
batch_diagrams/<migration name>/, and each is checked against the SHA-256 in
its record. A replay places them in data/math/diagrams next to the database it
changes, never anywhere else.

Write a migration from a finished batch with
    python backend/src/database/math/migrations/math_entry_record.py --write OUTPUT.py dist/math-batches/<id>/manifest.json
and run it with --db PATH, adding --apply after the preview. check_record()
replays it on a copy of a database that already has the batch (normally the
baseline option 8 brought home) to prove the record matches live.
"""
import argparse
import ast
from contextlib import closing, redirect_stdout
from datetime import datetime
import hashlib
import io
import json
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
import zipfile

BACKEND = Path(__file__).resolve().parents[4]
SOURCE = BACKEND / 'src'
for _path in (BACKEND, SOURCE):  # backend/ for the publishers, backend/src for the renderer
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))
import diagram_sync  # noqa: E402
from live_math_publication import publish  # noqa: E402
from preview_math_sync import read_entry  # noqa: E402
from migration_db import migration_target  # noqa: E402

ASSETS = 'batch_diagrams'
DONE = ('applied', 'already_present')


# ---- Reading a finished batch ----
def published_on(manifest):
    """The local date the batch's last entry was published (or confirmed already present)."""
    times = [h['at'] for name in manifest['order'] for h in manifest['entries'][name]['history']
             if h['operation'] in ('publish', 'live-check', 'reconcile')]
    if not times:
        raise ValueError('This batch has no recorded publication.')
    return datetime.fromisoformat(max(times)).astimezone().date()


def records_from_manifest(manifest):
    """Return (records, files) for the batch's published entries, in publish order.

    Each record is {canonical_name, title, slug, kind, payload}; files maps an SVG
    file name to its bytes. The packages must still be the ones that were reviewed.
    """
    left = [n for n in manifest['order'] if manifest['entries'][n]['state'] not in DONE]
    if left:
        raise ValueError('These entries of the batch are not live, so the batch cannot be recorded yet: ' +
                         ', '.join(left) + '. Finish the batch with option 20 first.')
    records, files = [], {}
    for name in manifest['order']:
        entry = manifest['entries'][name]
        data = Path(entry['package']).read_bytes()
        if hashlib.sha256(data).hexdigest() != entry['sha256']:
            raise ValueError(f'{name}: its package no longer matches the one that was reviewed and published '
                             f'({entry["package"]}). Nothing was written.')
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            json_name = next(n for n in archive.namelist() if n.endswith('.json'))
        if json_name == 'diagrams.json':
            payload, svgs = diagram_sync.unpack(data)
            kind = 'diagrams'
            for record in payload['diagrams']:
                files[diagram_sync.svg_name(record['source_hash'])] = svgs[record['source_hash']]
        else:
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                payload = json.loads(archive.read(json_name))
            kind = 'entry'
        if payload.get('canonical_name') != name:
            raise ValueError(f'{name}: its package is for {payload.get("canonical_name")}.')
        records.append(dict(canonical_name=name, title=entry['title'], slug=entry['slug'], kind=kind, payload=payload))
    return records, files


# ---- Writing the migration ----
TEMPLATE = '''r"""Entries of the option 20 batch "{name}" (batch {batch_id}).

Published on live on {date} with helper option 20, in this order, which is the
order of their ids on live:
{lines}
Replays them with math_entry_record, through the code the live publish used.
Preview with --db PATH; add --apply to write, after a backup. Never run it on
the working copy or on live: it is a record, and option 20 publishes.{assets}
"""
import json

from math_entry_record import main

ENTRIES = json.loads(r\'\'\'
{data}
\'\'\')

if __name__ == '__main__':
    main(ENTRIES, __doc__, __file__)
'''


def _plain(text):
    """Text safe inside the migration's raw docstring."""
    return ' '.join(str(text).replace('"""', "'''").split())


def migration_text(manifest, records, asset_folder):
    lines = ''.join(f'{i:>3}. {_plain(r["title"])} ({r["canonical_name"]})' +
                    (' [diagrams]' if r['kind'] == 'diagrams' else '') + '\n' for i, r in enumerate(records, 1))
    assets = ('\n\nIts diagram SVGs are in ' + asset_folder + '/.') if any(r['kind'] == 'diagrams' for r in records) else ''
    # A single quote only appears inside JSON strings, where \\u0027 means the same;
    # this keeps the data clear of the r\'\'\' delimiters.
    data = json.dumps(records, indent=1, ensure_ascii=False).replace("'", '\\u0027')
    return TEMPLATE.format(name=_plain(manifest['name']), batch_id=manifest['batch_id'],
                           date=published_on(manifest).isoformat(), lines=lines, assets=assets, data=data)


def write_migration(output, manifest):
    """Write the migration file and its SVGs (new files only). Return the paths written."""
    output = Path(output)
    records, files = records_from_manifest(manifest)
    folder = output.parent / ASSETS / output.stem
    text = migration_text(manifest, records, ASSETS + '/' + output.stem)
    written = []
    with output.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(text)
    written.append(output)
    if files:
        folder.mkdir(parents=True, exist_ok=True)
        for name, data in sorted(files.items()):
            path = folder / name
            if path.exists() and path.read_bytes() == data:
                continue
            with path.open('xb') as stream:
                stream.write(data)
            written.append(path)
    return written


def load_entries(path):
    """The ENTRIES list of a migration file, read as data (the file is not run)."""
    tree = ast.parse(Path(path).read_text(encoding='utf-8'))
    for node in tree.body:
        if isinstance(node, ast.Assign) and [getattr(t, 'id', None) for t in node.targets] == ['ENTRIES']:
            return json.loads(node.value.args[0].value)
    raise ValueError(f'{path} has no ENTRIES list.')


# ---- Replay ----
def package(record, asset_dir):
    """Rebuild the package bytes for one record, checking each SVG against its recorded SHA-256."""
    buffer = io.BytesIO()
    if record['kind'] == 'diagrams':
        files = {}
        for item in record['payload']['diagrams']:
            path = Path(asset_dir) / diagram_sync.svg_name(item['source_hash'])
            if not path.is_file():
                raise ValueError(f'{record["canonical_name"]}: diagram file missing: {path}')
            data = path.read_bytes()
            if hashlib.sha256(data).hexdigest() != item['sha256']:
                raise ValueError(f'{record["canonical_name"]}: {path} does not match its recorded SHA-256.')
            files[item['source_hash']] = data
        with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr('diagrams.json', json.dumps(record['payload'], ensure_ascii=False, indent=2))
            for item in record['payload']['diagrams']:
                archive.writestr('svg/' + diagram_sync.svg_name(item['source_hash']), files[item['source_hash']])
    else:
        with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr('entry.json', json.dumps(record['payload'], ensure_ascii=False, indent=2))
    return buffer.getvalue()


def entry_id(database, canonical):
    with closing(sqlite3.connect(Path(database).resolve().as_uri() + '?mode=ro', uri=True)) as db:
        row = db.execute('SELECT id FROM math_concepts WHERE canonical_name=?', (canonical,)).fetchone()
    return row[0] if row else None


def replay(database, records, asset_dir):
    """Publish each record into database in order, as live did. Return [(canonical, status, id)]."""
    database = Path(database)
    (database.parent / 'data' / 'math' / 'diagrams').mkdir(parents=True, exist_ok=True)
    results = []
    with tempfile.TemporaryDirectory(prefix='replay-backups-', ignore_cleanup_errors=True) as backups:
        for record in records:
            # The migration took its own backup; publish() also makes one per entry, in a
            # temporary folder, and its messages about those would only mislead.
            with redirect_stdout(io.StringIO()):
                result = publish(package(record, asset_dir), database, Path(backups), SOURCE)
            ident = entry_id(database, record['canonical_name'])
            print(f'{result["status"]}: {record["canonical_name"]} (id {ident})')
            results.append((record['canonical_name'], result['status'], ident))
    return results


def main(records, description, migration_file):
    migration = Path(migration_file).resolve()
    with migration_target(argparse.ArgumentParser(description=description)) as target:
        replay(target, records, migration.parent / ASSETS / migration.stem)


# ---- Checking a record against a database that has the batch ----
def _snapshot(source, destination):
    with closing(sqlite3.connect(Path(source).resolve().as_uri() + '?mode=ro', uri=True)) as src, \
            closing(sqlite3.connect(destination)) as dst:
        src.backup(dst)


def _content(database, canonical):
    """One entry as read_snapshot sees it, with its diagram rows (block order included)."""
    with closing(sqlite3.connect(Path(database).resolve().as_uri() + '?mode=ro', uri=True)) as db:
        entry = read_entry(db, canonical)
        rows = db.execute('SELECT d.block_index, d.source_hash, d.source_tex, d.svg_path FROM math_concept_diagrams d '
                          'JOIN math_concepts c ON c.id=d.concept_id WHERE c.canonical_name=? '
                          'ORDER BY d.block_index, d.source_hash', (canonical,)).fetchall()
    return entry, rows


def remove_entries(database, names):
    """Delete the named entries from a scratch copy, as if the batch had never been published.

    Raise ValueError if another entry points at one of them, since removing it
    would change that entry too.
    """
    with closing(sqlite3.connect(database)) as db:
        db.execute('PRAGMA foreign_keys=ON')
        ids = [db.execute('SELECT id FROM math_concepts WHERE canonical_name=?', (n,)).fetchone()[0] for n in names]
        marks = ','.join('?' * len(ids))
        tables = [n for (n,) in db.execute("SELECT name FROM sqlite_master WHERE type='table' "
                                           "AND name NOT LIKE 'sqlite_%' AND name != 'math_concepts'")]
        # Rows that belong to the batch's entries go with them.
        for table in tables:
            if 'concept_id' in [c[1] for c in db.execute(f'PRAGMA table_info("{table}")')]:
                db.execute(f'DELETE FROM "{table}" WHERE concept_id IN ({marks})', ids)
        # Anything else pointing at them would change if they went.
        for table in tables + ['math_concepts']:
            columns = [c[1] for c in db.execute(f'PRAGMA table_info("{table}")')]
            pointers = {fk[3] for fk in db.execute(f'PRAGMA foreign_key_list("{table}")') if fk[2] == 'math_concepts'}
            pointers |= {'related_concept_id'} & set(columns)
            owner = 'id' if table == 'math_concepts' else 'concept_id'
            for column in sorted(pointers - {'concept_id'}):
                hit = db.execute(f'SELECT {owner} FROM "{table}" WHERE "{column}" IN ({marks}) '
                                 f'AND {owner} NOT IN ({marks})', ids + ids).fetchone()
                if hit:
                    other = db.execute('SELECT canonical_name FROM math_concepts WHERE id=?', (hit[0],)).fetchone()
                    raise ValueError(f'{other[0] if other else hit[0]} points at an entry of the batch ({table}.{column})')
        db.execute(f'DELETE FROM math_concepts WHERE id IN ({marks})', ids)
        if db.execute("SELECT 1 FROM sqlite_master WHERE name='sqlite_sequence'").fetchone():
            db.execute("UPDATE sqlite_sequence SET seq=(SELECT coalesce(max(id), 0) FROM math_concepts) "
                       "WHERE name='math_concepts'")
        db.commit()


def check_record(records, asset_dir, reference):
    """Prove the record rebuilds the batch exactly as reference (a database with the batch) holds it.

    Works on scratch copies only. Return report lines; raise ValueError on any difference.
    """
    names = [r['canonical_name'] for r in records]
    expected = {n: _content(reference, n) for n in names}
    missing = [n for n in names if expected[n][0] is None]
    if missing:
        raise ValueError('Not in ' + str(reference) + ': ' + ', '.join(missing) +
                         '. Run option 8 after the batch, then try again.')
    live_ids = [entry_id(reference, n) for n in names]
    lines = []
    with tempfile.TemporaryDirectory(prefix='record-check-', ignore_cleanup_errors=True) as folder:
        copy = Path(folder) / 'before-batch' / 'catalog.db'
        copy.parent.mkdir()
        _snapshot(reference, copy)
        try:
            remove_entries(copy, names)
        except ValueError as error:
            raise ValueError('Could not rebuild the database as it was before the batch, because ' + str(error) +
                             '. Record this batch by hand (see "Record a batch in git" in CONTENT_SYNC.md).') from None
        results = replay(copy, records, asset_dir)
        if any(status != 'APPLIED' for _, status, _ in results):
            raise ValueError('The replay did not add every entry: ' +
                             ', '.join(f'{n} {s}' for n, s, _ in results if s != 'APPLIED'))
        differ = [n for n in names if _content(copy, n) != expected[n]]
        if differ:
            raise ValueError('The replay differs from the reference database for: ' + ', '.join(differ) +
                             '. Were these entries edited after the batch? Nothing was written.')
        ids = [ident for _, _, ident in results]
        if sorted(live_ids) != live_ids:
            raise ValueError('The entries do not have increasing ids in the reference database, so the publish '
                             'order is not the id order. Record this batch by hand.')
        lines.append(f'Replayed {len(records)} entries on a copy of {reference} with the batch removed: '
                     'every entry, its metadata and diagram rows match.')
        lines.append('Ids: ' + ('identical to the reference (' + ', '.join(map(str, ids)) + ')' if ids == live_ids
                                else f'in the same order; the reference has {live_ids}, the replay {ids}'))
        shutil.rmtree(copy.parent / 'data', ignore_errors=True)
    return lines


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', required=True, help='New migration file to create')
    parser.add_argument('manifest', help='dist/math-batches/<batch id>/manifest.json of a finished option 20 batch')
    arguments = parser.parse_args()
    paths = write_migration(arguments.write, json.loads(Path(arguments.manifest).read_text(encoding='utf-8')))
    print('Wrote', *paths, sep='\n  ')
