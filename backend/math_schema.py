"""The one-time math schema upgrade for retiring and merging entries.

Adds to math_concepts the nullable columns retired_at (NULL = active),
retired_into_id (the survivor) and retirement_reason; a case-insensitive
unique index on slug, so the database itself reserves every URL; the
math_concept_merges log; and math_schema_meta, which records the reader
contract version that the live retirements need (see
backend/src/services/math/retirement.py).

The same upgrade function serves the reviewed schema package published
with options 3-5, the add_math_retirement_columns migration and option 8,
which upgrades temporary copies of the laptop databases to compare them
with an upgraded live database. Running it twice changes nothing. Any part
that already exists must match its expected definition exactly; anything
else stops the whole upgrade, as do slugs that differ only in case or
surrounding spaces.

This module is sent to the server over SSH, so it uses only the standard
library.
"""
from contextlib import closing
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import uuid

KIND = 'math-schema'
VERSION = 1

# (name, declared type, (referenced table, column) or None)
COLUMNS = (
    ('retired_at', 'TEXT', None),
    ('retired_into_id', 'INTEGER', ('math_concepts', 'id')),
    ('retirement_reason', 'TEXT', None),
)
COLUMN_SQL = {
    'retired_at': 'ALTER TABLE math_concepts ADD COLUMN retired_at TEXT',
    'retired_into_id': 'ALTER TABLE math_concepts ADD COLUMN retired_into_id INTEGER REFERENCES math_concepts(id)',
    'retirement_reason': 'ALTER TABLE math_concepts ADD COLUMN retirement_reason TEXT',
}
# Stored verbatim in sqlite_master, so each must stay byte-identical once published.
OBJECT_SQL = {
    'idx_math_concepts_slug_ci': 'CREATE UNIQUE INDEX idx_math_concepts_slug_ci ON math_concepts(lower(slug))',
    'math_concept_merges': (
        'CREATE TABLE math_concept_merges (\n'
        '    id INTEGER PRIMARY KEY AUTOINCREMENT,\n'
        '    absorbed_id INTEGER NOT NULL REFERENCES math_concepts(id),\n'
        '    survivor_id INTEGER REFERENCES math_concepts(id),\n'
        '    applied_at TEXT NOT NULL,\n'
        '    undone_at TEXT,\n'
        '    reason TEXT NOT NULL,\n'
        '    survivor_before_json TEXT,\n'
        '    survivor_after_json TEXT,\n'
        '    added_rows_json TEXT NOT NULL,\n'
        '    package_sha256 TEXT NOT NULL\n'
        ')'),
    'math_schema_meta': 'CREATE TABLE math_schema_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)',
}
CONTRACT_KEY = 'retirement_contract_required'


def inspect(db):
    """Return {'missing': [parts to create], 'problems': [why the upgrade must stop]}; never writes."""
    missing, problems = [], []
    columns = {row[1]: row for row in db.execute('PRAGMA table_info(math_concepts)')}
    if not columns:
        return dict(missing=[], problems=['no math_concepts table'])
    references = {row[3]: (row[2], row[4]) for row in db.execute('PRAGMA foreign_key_list(math_concepts)')}
    for name, declared, reference in COLUMNS:
        if name not in columns:
            missing.append(name)
            continue
        row = columns[name]
        if (row[2].upper() != declared or row[3] or row[4] is not None or row[5]
                or references.get(name) != reference):
            problems.append(f'math_concepts.{name} exists with a different definition')
    stored = dict(db.execute("SELECT name, sql FROM sqlite_master WHERE name IN (?, ?, ?)", tuple(OBJECT_SQL)))
    for name, sql in OBJECT_SQL.items():
        if name not in stored:
            missing.append(name)
        elif stored[name] != sql:
            problems.append(f'{name} exists with a different definition')
    if 'math_schema_meta' in stored and stored['math_schema_meta'] == OBJECT_SQL['math_schema_meta']:
        value = db.execute('SELECT value FROM math_schema_meta WHERE key = ?', (CONTRACT_KEY,)).fetchone()
        if value is None:
            missing.append(CONTRACT_KEY)
        elif not value[0].isdigit():
            problems.append(f'{CONTRACT_KEY} is not a whole number')
    if 'slug' not in columns:
        problems.append('math_concepts has no slug column')
    elif 'idx_math_concepts_slug_ci' in missing:
        problems += slug_collisions(db)
    return dict(missing=missing, problems=problems)


def slug_collisions(db):
    """Describe slugs shared by several entries when compared ignoring case or surrounding spaces."""
    found = []
    for expression in ('lower(slug)', 'lower(trim(slug))'):
        for key, names in db.execute(f'SELECT {expression}, group_concat(canonical_name, ", ") FROM math_concepts '
                                     f'GROUP BY {expression} HAVING count(*) > 1'):
            found.append(f'slug {key!r} is shared by {names}')
    return sorted(set(found))


def state(db):
    """'current', 'absent' (no part of the upgrade yet), 'partial' or 'invalid'."""
    result = inspect(db)
    if result['problems']:
        return 'invalid'
    if not result['missing']:
        return 'current'
    # Without the meta table its row is not listed as missing separately.
    every_part = [name for name, _, _ in COLUMNS] + list(OBJECT_SQL)
    return 'absent' if set(result['missing']) >= set(every_part) else 'partial'


def upgrade(db):
    """Create whatever part of the upgrade is missing, inside the caller's transaction.

    Return the statements run (none when already current). Raise ValueError,
    having changed nothing, if any existing part differs or slugs collide.
    """
    result = inspect(db)
    if result['problems']:
        raise ValueError('Schema upgrade stopped; nothing changed: ' + '; '.join(result['problems']))
    statements = [COLUMN_SQL[name] for name, _, _ in COLUMNS if name in result['missing']]
    statements += [OBJECT_SQL[name] for name in OBJECT_SQL if name in result['missing']]
    for statement in statements:
        db.execute(statement)
    if CONTRACT_KEY in result['missing'] or 'math_schema_meta' in result['missing']:
        statement = f"INSERT INTO math_schema_meta (key, value) VALUES ('{CONTRACT_KEY}', '0')"
        db.execute(statement)
        statements.append(statement)
    after = inspect(db)
    if after['missing'] or after['problems']:
        raise ValueError('Schema upgrade did not verify: ' + '; '.join(after['missing'] + after['problems']))
    return statements


def required_contract(db):
    """The reader contract version live retirements need: 0 before the upgrade or any retirement."""
    if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='math_schema_meta'").fetchone():
        return 0
    row = db.execute('SELECT value FROM math_schema_meta WHERE key = ?', (CONTRACT_KEY,)).fetchone()
    return int(row[0]) if row and row[0].isdigit() else 0


def payload():
    """The schema package's whole content; the statements come from this module, never the package."""
    return dict(kind=KIND, version=VERSION)


def validate_payload(data):
    if data != payload():
        raise ValueError('Invalid schema upgrade package.')


def review(data):
    validate_payload(data)
    lines = ['Proposed operation: one-time math schema upgrade for retiring and merging entries',
             'Adds only what is missing; existing parts must match exactly. No entry is changed.']
    lines += ['  ' + sql.replace('\n', ' ') for sql in list(COLUMN_SQL.values()) + list(OBJECT_SQL.values())]
    lines.append(f"  INSERT INTO math_schema_meta (key, value) VALUES ('{CONTRACT_KEY}', '0')")
    return '\n'.join(lines)


def status(database, connection=None):
    """One-line verdict on applying the upgrade to database; never writes."""
    with (closing(sqlite3.connect(Path(database).resolve().as_uri() + '?mode=ro', uri=True))
          if connection is None else _borrowed(connection)) as db:
        result = inspect(db)
    if result['problems']:
        return 'BLOCKED — ' + '; '.join(result['problems'])
    if not result['missing']:
        return 'ALREADY PRESENT — the schema is already upgraded'
    return 'ELIGIBLE — the upgrade will add: ' + ', '.join(result['missing'])


class _borrowed:
    """Context manager that lends an open connection without closing it."""

    def __init__(self, connection):
        self.connection = connection

    def __enter__(self):
        return self.connection

    def __exit__(self, *exc):
        return False


def apply(database, data, backup_dir):
    """Publish the upgrade: verified backup, upgrade and checks in one transaction."""
    validate_payload(data)
    backup_dir = Path(backup_dir)
    with closing(sqlite3.connect(Path(database).resolve().as_uri() + '?mode=rw', uri=True, timeout=10)) as db:
        db.execute('PRAGMA foreign_keys=ON')
        db.execute('BEGIN IMMEDIATE')
        verdict = status(database, connection=db)
        if verdict.startswith('ALREADY PRESENT'):
            return dict(status='ALREADY_PRESENT', canonical='Math schema upgrade', backup=None)
        if not verdict.startswith('ELIGIBLE'):
            raise ValueError(verdict)
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup = backup_dir / ('before-math-schema-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
                               + '-' + uuid.uuid4().hex[:8] + '.db')
        with backup.open('xb'):
            pass
        # The write lock held above keeps the database unchanged while it is copied.
        with closing(sqlite3.connect(Path(database).resolve().as_uri() + '?mode=ro', uri=True)) as source, \
                closing(sqlite3.connect(backup)) as destination:
            source.backup(destination)
            if destination.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                raise ValueError('Backup failed integrity check.')
        upgrade(db)
        if db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok' or db.execute('PRAGMA foreign_key_check').fetchone():
            raise ValueError('Database check failed after the upgrade; rolled back.')
        db.commit()
    return dict(status='APPLIED', canonical='Math schema upgrade', backup=str(backup))


def write_package(path):
    """Write the schema package ZIP to a new file at path."""
    import zipfile
    with zipfile.ZipFile(path, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(KIND + '.json', json.dumps(payload(), indent=2))
