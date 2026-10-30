"""Replay merges, plain retirements and undos published with helper option 21.

Shared by the merge_entries_<date>.py migrations. Each lists the change sets
from its session receipts (dist/merge-sessions/<id>/receipt.json, the
"change_set" field), in the order they were published on live. For a merge,
replay() first brings the survivor to the approved version recorded in the
change set (its text and synonyms, published beforehand with options 2-5),
then applies the change set with merge_sync.replay, the code the live publish
used, and verifies it. Change sets already recorded are skipped, so a
migration can run again. Needs add_math_retirement_columns.py first.

Write a migration from receipts with
    python backend/src/database/math/migrations/math_entry_merge.py --write OUTPUT.py RECEIPT.json [...]
and run it with --db PATH, adding --apply after the preview.
"""
import argparse
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))  # backend/, for merge_sync
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # backend/src, for the renderer
from apply_math_text_patch import PATCH_FIELDS, write_metadata  # noqa: E402
import math_schema  # noqa: E402
import merge_sync  # noqa: E402
from migration_db import migration_target  # noqa: E402



def recorded(db, change_set):
    if change_set['action'] == 'undo':
        row = merge_sync.log_row(db, change_set['merge']['package_sha256'])
        return row is not None and row[1] is not None
    return merge_sync.log_row(db, change_set['package_sha256']) is not None


def label(change_set):
    if change_set['action'] == 'undo':
        return 'undo of the ' + change_set['merge']['action'] + ' of ' + change_set['merge']['absorbed']
    return change_set['action'] + ' of ' + change_set['absorbed'] + (
        ' into ' + change_set['survivor'] if change_set['survivor'] else '')


def survivor_text(db, change_set):
    """Give the survivor its approved text and details (as options 2-5 publish them), unless it has them already."""
    from services.math.concept_render_service import render_tex_reusing_existing_diagrams
    name = change_set['survivor']
    strip = lambda entry: {k: v for k, v in entry.items() if k != 'diagrams'}  # noqa: E731
    before, after = (strip(json.loads(change_set[key])) for key in ('survivor_before_json', 'survivor_after_json'))
    current = merge_sync.read_entry(db, name)
    if current == after:
        return
    if current != before:
        raise ValueError(f'{name} matches neither its recorded version before the merge nor the approved one.')
    if {key for key in after if after[key] != before[key]} - PATCH_FIELDS:
        raise ValueError(f'{name} changed its slug; record that change in its own migration first.')
    ident = merge_sync.ident(db, name)
    rendered = render_tex_reusing_existing_diagrams(ident, after['cleaned_tex'], db.cursor())
    db.execute("UPDATE math_concepts SET cleaned_tex = ?, rendered_tex = ?, updated_at = datetime('now') WHERE id = ?",
               (after['cleaned_tex'], rendered, ident))
    write_metadata(db, ident, before, after)


def replay(database, change_sets):
    """Apply the change sets in order, in one transaction."""
    with closing(sqlite3.connect(database)) as db:
        db.execute('PRAGMA foreign_keys=ON')
        db.execute('BEGIN IMMEDIATE')
        if math_schema.state(db) != 'current':
            raise SystemExit('Run add_math_retirement_columns.py first.')
        for change_set in change_sets:
            if recorded(db, change_set):
                print('Already recorded:', label(change_set))
                continue
            if change_set['action'] == 'merge':
                survivor_text(db, change_set)
            merge_sync.replay(db, change_set)
            merge_sync.verify(db, change_set)
            print('Replayed:', label(change_set))
        if db.execute('PRAGMA foreign_key_check').fetchone():
            raise ValueError('Foreign key check failed; nothing saved.')
        db.commit()


def main(change_sets, description):
    with migration_target(argparse.ArgumentParser(description=description)) as target:
        replay(target, change_sets)


TEMPLATE = '''"""{title}

Published on live with helper option 21, in this order:
{lines}
Replays them with math_entry_merge (run add_math_retirement_columns.py first).
"""
import json

from math_entry_merge import main

CHANGE_SETS = json.loads(r\'\'\'
{data}
\'\'\')

if __name__ == '__main__':
    main(CHANGE_SETS, __doc__)
'''


def write_migration(output, receipts):
    change_sets = [json.loads(Path(path).read_text(encoding='utf-8'))['change_set'] for path in receipts]
    data = json.dumps(change_sets, indent=1, ensure_ascii=False)
    if "'''" in data:
        raise ValueError('A change set contains three quotes in a row; write this migration by hand.')
    text = TEMPLATE.format(title='Merges and retirements of math entries.',
                           lines=''.join(f'- {label(c)} ({c["at"]})\n' for c in change_sets), data=data)
    with open(output, 'x', encoding='utf-8') as stream:
        stream.write(text)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', required=True, help='New migration file to create')
    parser.add_argument('receipts', nargs='+', help='Option 21 receipts, in the order they were published')
    arguments = parser.parse_args()
    write_migration(arguments.write, arguments.receipts)
    print('Wrote', arguments.write)
