"""Read-only three-way comparison of math content. Never applies changes."""
import argparse
from collections import Counter
from contextlib import closing, nullcontext
import json
from pathlib import Path
import sqlite3


def read_snapshot(path, connection=None):
    result = {}
    with (nullcontext(connection) if connection is not None else closing(sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro', uri=True))) as db:
        db.row_factory = sqlite3.Row
        if not db.in_transaction:
            db.execute('BEGIN')  # A consistent view even if a local writer is active.
        if db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise ValueError('Database integrity check failed.')
        if db.execute('PRAGMA foreign_key_check').fetchone():
            raise ValueError('Database has broken foreign keys.')
        for row in db.execute('SELECT id, canonical_name, slug, title, owner, cleaned_tex, is_cleaned FROM math_concepts'):
            item = dict(row)
            ident = item.pop('id')
            key = item.pop('canonical_name')
            if not key or key in result:
                raise ValueError('Missing or duplicate canonical name.')
            queries = {
                'classifications': 'SELECT c.code FROM math_classifications c JOIN math_concept_classifications m ON c.id=m.classification_id WHERE m.concept_id=?',
                'types': 'SELECT t.type_name FROM math_types t JOIN math_concept_types m ON t.id=m.type_id WHERE m.concept_id=?',
                'synonyms': 'SELECT synonym_text FROM math_synonyms WHERE concept_id=?',
                'definitions': 'SELECT defined_term FROM math_definitions WHERE concept_id=?',
                'link_exclusions': 'SELECT word FROM math_link_exclusions WHERE concept_id=?',
                'related_concepts': 'SELECT related_canonical_name FROM math_related_concepts WHERE concept_id=?',
            }
            for name, query in queries.items():
                item[name] = sorted((r[0] for r in db.execute(query,(ident,))), key=lambda v: (v is not None, v or ''))
            result[key] = item
    return result


def compare(base, local, live):
    changes = []
    for key in sorted(base.keys() | local.keys() | live.keys()):
        b, l, r = base.get(key), local.get(key), live.get(key)
        if b == l == r:
            continue
        if l == r:
            status = 'already_equal'
        elif l == b:
            status = 'live_only_preserve'
        elif r == b:
            status = 'local_only_review'
        else:
            status = 'conflict'
        fields = []
        for field in sorted(set(b or {}) | set(l or {}) | set(r or {})):
            values = [(v or {}).get(field) for v in (b,l,r)]
            if not values[0] == values[1] == values[2]:
                fields.append(dict(field=field, base=values[0], local=values[1], live=values[2]))
        changes.append(dict(canonical_name=key, status=status,
                            present=dict(base=b is not None, local=l is not None, live=r is not None),
                            requires_manual_deletion_review=b is not None and (l is None or r is None),
                            fields=fields))
    return dict(read_only=True, summary=dict(Counter(c['status'] for c in changes)), changes=changes)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('base','local','live','output'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    report = compare(*(read_snapshot(p) for p in (args.base,args.local,args.live)))
    # Exclusive creation: never overwrite a snapshot or an earlier report.
    with args.output.open('x',encoding='utf-8') as out:
        json.dump(report,out,ensure_ascii=False,indent=2)
    print('Read-only preview complete. No database was modified.')
    print(json.dumps(report['summary']))


if __name__ == '__main__':
    main()
