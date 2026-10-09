"""Apply one reviewed, text-only math patch. Run on the host from a private folder."""
import argparse
from contextlib import closing
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import sys
import uuid
from preview_math_sync import read_snapshot
from publish_math_entry import validate as validate_entry


def patch_intended(payload):
    required = {'canonical_name', 'expected', 'replacement_tex'}
    if not isinstance(payload, dict) or not required <= payload.keys() or set(payload) - required - {'replacement_synonyms'}:
        raise ValueError('Invalid existing-entry patch fields.')
    expected = payload['expected']
    if not isinstance(expected, dict):
        raise ValueError('Invalid expected entry.')
    canonical = payload['canonical_name']
    validate_entry(dict(expected, canonical_name=canonical))
    intended = dict(expected, cleaned_tex=payload['replacement_tex'])
    if 'replacement_synonyms' in payload:
        intended['synonyms'] = payload['replacement_synonyms']
    validate_entry(dict(intended, canonical_name=canonical))
    aliases = intended['synonyms']
    if len({s.casefold() for s in aliases}) != len(aliases):
        raise ValueError('Duplicate synonyms ignoring case.')
    intended['synonyms'] = sorted(aliases)
    return intended


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
    if extract_all_pstricks_diagram_blocks(expected['cleaned_tex']) != extract_all_pstricks_diagram_blocks(replacement):
        raise ValueError('Diagram changes are outside this text-only updater.')
    backup_dir.mkdir(parents=True,exist_ok=True)
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
    backup=backup_dir/('before-math-update-'+stamp+'.db')
    with closing(sqlite3.connect(database.resolve().as_uri()+'?mode=rw',uri=True,timeout=10)) as db:
        db.execute('BEGIN IMMEDIATE')
        current=read_snapshot(database,connection=db).get(canonical)
        if current != expected:
            raise ValueError('Conflict: live entry no longer matches the reviewed snapshot. Nothing changed.')
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
        if 'replacement_synonyms' in payload:
            db.execute('DELETE FROM math_synonyms WHERE concept_id=?', (ident,))
            db.executemany('INSERT INTO math_synonyms(concept_id,synonym_text) VALUES(?,?)',
                           [(ident, synonym) for synonym in intended['synonyms']])
        after=read_snapshot(database,connection=db)[canonical]
        if after != intended:
            raise ValueError('Verification failed. Update rolled back.')
        db.commit()
    print('Applied one content/synonym update:',canonical)
    print('Verified backup:',backup)
    return backup


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('patch',type=Path)
    parser.add_argument('--root',type=Path,default=Path.home()/'chi-portfolio')
    args=parser.parse_args()
    apply_patch(args.root/'backend/portfolio.db',json.loads(args.patch.read_text(encoding='utf-8')),
                args.root.parent/'backups',args.root/'backend/src')
