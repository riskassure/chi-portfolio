"""Database selection, preview and backup shared by the historical math migrations.

These scripts predate the helper and write directly to whichever database
they are given. There is deliberately no default: the old default,
backend/portfolio.db, is a stale copy, not the helper's working copy.

By default a script only previews. It runs against a temporary copy and
reports which entries it would add or change, leaving the database alone.
With --apply it first takes a verified backup, then changes the database.
Apply only to a local working database that nothing else is writing to.
"""
import argparse
from collections import Counter
from contextlib import closing, contextmanager
from datetime import datetime
import gc
from pathlib import Path
import sqlite3
import sys
import tempfile

# Labels for the per-entry tables a migration can touch.
LABELS = {
    'math_related_concepts': 'related links',
    'math_synonyms': 'synonyms',
    'math_definitions': 'defined terms',
    'math_concept_types': 'types',
    'math_concept_classifications': 'classifications',
    'math_link_exclusions': 'link exclusions',
    'math_concept_diagrams': 'diagrams',
}
# Columns of math_concepts that change as a consequence of a text change.
DERIVED_COLUMNS = {'rendered_tex', 'updated_at'}
COLUMN_LABELS = {'cleaned_tex': 'text'}


def existing_database(value):
    """Argparse type: an existing SQLite file that holds the math catalog."""
    path = Path(value)
    if not path.is_file():
        raise argparse.ArgumentTypeError(f'no database file at {path}')
    try:
        # Read-only, so a bad path can never create or change a file here.
        with closing(_read_only(path)) as connection:
            has_catalog = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='math_concepts'"
            ).fetchone()
    except sqlite3.DatabaseError as error:
        raise argparse.ArgumentTypeError(f'{path} is not a readable SQLite database ({error})')
    if not has_catalog:
        raise argparse.ArgumentTypeError(f'{path} has no math_concepts table')
    return path


def add_db_argument(parser):
    parser.add_argument(
        '--db', type=existing_database, required=True,
        help='SQLite database to change. Required; there is no default.')


@contextmanager
def migration_target(parser, argv=None):
    """Yield the database path the migration should write to.

    Without --apply this is a temporary copy, and the changes made to it are
    reported when the block ends. With --apply it is the real database, after
    a verified backup has been written beside it.
    """
    add_db_argument(parser)
    parser.add_argument(
        '--apply', action='store_true',
        help='Back up the database, then change it. Without this, only preview.')
    args = parser.parse_args(argv)
    db = args.db.resolve()
    print(f'Database: {db}')
    if args.apply:
        backup = create_backup(db, Path(sys.argv[0]).stem or 'migration')
        print(f'Backup: {backup}')
        try:
            yield db
        except BaseException:
            print(f'The migration failed. Some scripts commit in stages, so part of it may '
                  f'be saved. Backup taken before the run: {backup}. Before restoring it, stop '
                  f'everything that writes to the database and check for changes made since '
                  f'the backup; restoring discards them.', file=sys.stderr)
            raise
        print('Applied.')
        return
    with tempfile.TemporaryDirectory(prefix='migration-preview-', ignore_cleanup_errors=True) as folder:
        # Compare against a fixed snapshot, not the live file, so edits other
        # writers make to the database meanwhile are not reported as the script's.
        start = Path(folder) / ('start-' + db.name)
        copy = Path(folder) / db.name
        _snapshot(db, start)
        _snapshot(start, copy)
        try:
            yield copy
        except BaseException:
            print(f'Preview failed. Nothing was written to {db}.', file=sys.stderr)
            raise
        finally:
            # Scripts leave connections to the copy for the garbage collector;
            # close them so Windows can delete the temporary folder.
            gc.collect()
        print()
        print(f'PREVIEW ONLY. Nothing was written to {db}.')
        print('\n'.join(describe_changes(start, copy)))
        print('Run again with --apply to make these changes, after a backup.')


def create_backup(db, label):
    """Write a verified SQLite backup of db into a backups folder beside it."""
    folder = db.parent / 'backups'
    folder.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    backup = folder / f'{db.stem}.before-{label}-{stamp}{db.suffix or ".db"}'
    _snapshot(db, backup)
    return backup


def _snapshot(source, destination):
    # Exclusive creation never overwrites an existing file, even via a symlink.
    with destination.open('xb'):
        pass
    with closing(_read_only(source)) as src, closing(sqlite3.connect(destination)) as dst:
        src.backup(dst)
        if dst.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise RuntimeError(f'Backup failed its integrity check: {destination}')


def _read_only(path):
    return sqlite3.connect(Path(path).resolve().as_uri() + '?mode=ro', uri=True)


def describe_changes(before_path, after_path):
    """Plain-language lines listing what differs between two catalog databases."""
    with closing(_read_only(before_path)) as before, closing(_read_only(after_path)) as after:
        old_concepts = _concepts(before)
        new_concepts = _concepts(after)
        slugs = {row['id']: row['slug'] for row in new_concepts.values()}
        slugs.update({row['id']: row['slug'] for row in old_concepts.values()})
        added = sorted(set(new_concepts) - set(old_concepts))
        removed = sorted(set(old_concepts) - set(new_concepts))
        changes = {}
        for slug in set(old_concepts) & set(new_concepts):
            old, new = old_concepts[slug], new_concepts[slug]
            columns = [c for c in old if c != 'id' and old[c] != new[c]]
            if set(columns) - DERIVED_COLUMNS:
                columns = [c for c in columns if c not in DERIVED_COLUMNS]
            for column in columns:
                changes.setdefault(slug, []).append(COLUMN_LABELS.get(column, column))
        other = []
        for table in _tables(before) | _tables(after):
            if table == 'math_concepts':
                continue
            old_rows, new_rows = _rows(before, table), _rows(after, table)
            label = LABELS.get(table, table)
            if 'concept_id' in _columns(after if new_rows is not None else before, table):
                for concept_id, (plus, minus) in _per_concept(old_rows, new_rows).items():
                    slug = slugs.get(concept_id, f'concept {concept_id}')
                    if slug in added:
                        continue
                    changes.setdefault(slug, []).append(_count(label, plus, minus))
            else:
                plus, minus = _difference(old_rows, new_rows)
                if plus or minus:
                    other.append(_count(label, plus, minus))
    lines = [f'New entries ({len(added)}): ' + (', '.join(added) or 'none')]
    if removed:
        lines.append(f'Removed entries ({len(removed)}): ' + ', '.join(removed))
    lines.append(f'Existing entries changed ({len(changes)})' + (':' if changes else ': none'))
    lines += [f'  {slug}: ' + ', '.join(parts) for slug, parts in sorted(changes.items())]
    if other:
        lines.append('Other tables: ' + '; '.join(sorted(other)))
    return lines


def _concepts(connection):
    connection.row_factory = sqlite3.Row
    rows = connection.execute('SELECT * FROM math_concepts').fetchall()
    connection.row_factory = None
    return {row['slug']: dict(row) for row in rows}


def _tables(connection):
    return {name for (name,) in connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}


def _columns(connection, table):
    return [row[1] for row in connection.execute(f'PRAGMA table_info("{table}")')]


def _rows(connection, table):
    """Rows of a table without its own id, so renumbering is not a change."""
    if table not in _tables(connection):
        return None
    columns = [c for c in _columns(connection, table) if c != 'id']
    if not columns:
        return []
    names = ', '.join(f'"{c}"' for c in columns)
    return [dict(zip(columns, row)) for row in
            connection.execute(f'SELECT {names} FROM "{table}"')]


def _key(row):
    return tuple(sorted((k, repr(v)) for k, v in row.items()))


def _difference(old_rows, new_rows):
    old = Counter(_key(r) for r in old_rows or [])
    new = Counter(_key(r) for r in new_rows or [])
    return sum((new - old).values()), sum((old - new).values())


def _per_concept(old_rows, new_rows):
    groups = {}
    for which, rows in ((0, old_rows or []), (1, new_rows or [])):
        for row in rows:
            groups.setdefault(row['concept_id'], ([], []))[which].append(row)
    result = {}
    for concept_id, (old, new) in groups.items():
        plus, minus = _difference(old, new)
        if plus or minus:
            result[concept_id] = (plus, minus)
    return result


def _count(label, plus, minus):
    parts = [f'+{plus}'] if plus else []
    parts += [f'-{minus}'] if minus else []
    return f'{label} ' + ' '.join(parts)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='List what differs between two math databases, such as a backup and the database now.')
    parser.add_argument('before', type=existing_database)
    parser.add_argument('after', type=existing_database)
    args = parser.parse_args()
    print('\n'.join(describe_changes(args.before, args.after)))
