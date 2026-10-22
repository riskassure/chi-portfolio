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


def patch_intended(payload):
    """Return the entry a content/synonym patch produces, or raise ValueError if it is unsafe.

    Only what the patch changes is validated, so an existing entry with missing
    classifications or duplicate unchanged metadata can still take a text fix.
    Diagrams and images must stay byte-identical (see media_fragments).
    """
    required = {'canonical_name', 'expected', 'replacement_tex'}
    if not isinstance(payload, dict) or not required <= payload.keys() or set(payload) - required - {'replacement_synonyms'}:
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
    if 'replacement_synonyms' in payload:
        aliases = payload['replacement_synonyms']
        if not isinstance(aliases, list) or any(not isinstance(v, str) or not v.strip() or v != v.strip()
                                                 for v in aliases) or len(set(aliases)) != len(aliases):
            raise ValueError('Invalid metadata: synonyms')
        if len({s.casefold() for s in aliases}) != len(aliases):
            raise ValueError('Duplicate synonyms ignoring case.')
        intended['synonyms'] = sorted(aliases)
    return intended


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
