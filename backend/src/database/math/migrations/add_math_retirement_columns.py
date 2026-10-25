"""Add the schema for retiring and merging math entries (the same upgrade as on live).

Adds retired_at, retired_into_id and retirement_reason to math_concepts, a
case-insensitive unique index on slug, the math_concept_merges log and
math_schema_meta. It is the upgrade the helper's schema package published on
live (backend/math_schema.py holds the one definition both use), so a
database rebuilt from the pipeline and these migrations, in order, matches
live. Running it again changes nothing; any part that exists with another
definition, or slugs that collide ignoring case, stop it before any change.

    python backend/src/database/math/migrations/add_math_retirement_columns.py --db PATH [--apply]
"""
import argparse
from contextlib import closing
from pathlib import Path
import sqlite3
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))  # backend/, for math_schema
import math_schema  # noqa: E402
from migration_db import migration_target  # noqa: E402


def migrate(database):
    with closing(sqlite3.connect(database)) as db:
        db.execute('BEGIN IMMEDIATE')
        statements = math_schema.upgrade(db)
        db.commit()
    print('\n'.join(statements) if statements else 'The schema is already upgraded; nothing to do.')


if __name__ == '__main__':
    with migration_target(argparse.ArgumentParser(description=__doc__)) as target:
        migrate(target)
