"""Prepare or apply one new, text-only math entry; never replace a database."""
import argparse
from contextlib import closing
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shutil
import sqlite3
import sys
import uuid
from preview_math_sync import read_snapshot


def validate(entry):
    required = {'canonical_name','slug','title','owner','cleaned_tex','is_cleaned',
                'classifications','types','synonyms','definitions','link_exclusions','related_concepts'}
    if not isinstance(entry,dict) or set(entry)!=required:
        raise ValueError('Invalid entry fields.')
    for key in ('canonical_name','slug','title','owner','cleaned_tex'):
        if not isinstance(entry[key],str) or not entry[key].strip():
            raise ValueError('Missing text field: '+key)
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',entry['slug']):
        raise ValueError('Use a lowercase, hyphenated URL slug.')
    if type(entry['is_cleaned']) is not int or entry['is_cleaned'] not in (0,1):
        raise ValueError('Invalid cleaned flag.')
    for key in required-{'canonical_name','slug','title','owner','cleaned_tex','is_cleaned'}:
        values=entry[key]
        if not isinstance(values,list) or any(not isinstance(v,str) or not v.strip() or v!=v.strip() for v in values) or len(set(values))!=len(values):
            raise ValueError('Invalid metadata: '+key)
    if not entry['classifications'] or not entry['types']:
        raise ValueError('Include classification and document type.')
    # This first increment deliberately excludes asset transfer and diagram generation.
    if re.search(r'\\(?:includegraphics|input|include|pstree|pspicture)|\\begin\s*\{(?:pspicture\*?|tikzpicture|figure\*?)\}|<\s*(?:img|svg|script|iframe)\b|/api/math/diagrams/',entry['cleaned_tex'],re.I):
        raise ValueError('Media/diagrams are outside this text-only publisher.')


def check_target(db, entry):
    for column in ('canonical_name','slug','title'):
        if db.execute(f'SELECT 1 FROM math_concepts WHERE lower(trim({column}))=lower(trim(?))',(entry[column],)).fetchone():
            raise ValueError('Duplicate '+column+'; nothing added.')
    for table,column in [('math_synonyms','synonym_text'),('math_definitions','defined_term')]:
        if db.execute(f'SELECT 1 FROM {table} WHERE lower(trim({column}))=lower(trim(?))',(entry['title'],)).fetchone():
            raise ValueError('Title already appears as a synonym/defined term; review it first.')
    for key,table,column in [('classifications','math_classifications','code'),('types','math_types','type_name'),('related_concepts','math_concepts','canonical_name')]:
        for value in entry[key]:
            if not db.execute(f'SELECT 1 FROM {table} WHERE {column}=?',(value,)).fetchone():
                raise ValueError(f'Missing live {key}: {value}')


def apply(database, entry, backup_dir, source_dir):
    validate(entry)
    sys.path.insert(0,str(source_dir.resolve()))
    from services.math.render_helper import render_prose_latex_to_html, extract_all_pstricks_diagram_blocks
    if extract_all_pstricks_diagram_blocks(entry['cleaned_tex']):
        raise ValueError('Diagrams are unsupported in this increment.')
    rendered=render_prose_latex_to_html(entry['cleaned_tex'])
    with closing(sqlite3.connect(database.resolve().as_uri()+'?mode=rw',uri=True,timeout=10)) as db:
        db.execute('PRAGMA foreign_keys=ON')
        db.execute('BEGIN IMMEDIATE')
        check_target(db,entry)
        backup_dir.mkdir(parents=True,exist_ok=True)
        backup=backup_dir/('before-new-entry-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]+'.db')
        with backup.open('xb'): pass
        with closing(sqlite3.connect(database.resolve().as_uri()+'?mode=ro',uri=True)) as src:
            with closing(sqlite3.connect(backup)) as dst:
                src.backup(dst)
                if dst.execute('PRAGMA integrity_check').fetchone()[0]!='ok':
                    raise ValueError('Backup failed verification.')
        now=datetime.now(timezone.utc).isoformat()
        cursor=db.execute('INSERT INTO math_concepts(canonical_name,slug,title,owner,cleaned_tex,is_cleaned,rendered_tex,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)',
                          tuple(entry[k] for k in ('canonical_name','slug','title','owner','cleaned_tex','is_cleaned'))+(rendered,now,now))
        ident=cursor.lastrowid
        for key,table,lookup,column,fk in [('classifications','math_concept_classifications','math_classifications','code','classification_id'),('types','math_concept_types','math_types','type_name','type_id')]:
            for value in entry[key]:
                target=db.execute(f'SELECT id FROM {lookup} WHERE {column}=?',(value,)).fetchone()[0]
                db.execute(f'INSERT INTO {table}(concept_id,{fk}) VALUES(?,?)',(ident,target))
        for key,table,column in [('synonyms','math_synonyms','synonym_text'),('definitions','math_definitions','defined_term'),('link_exclusions','math_link_exclusions','word')]:
            for value in entry[key]:
                db.execute(f'INSERT INTO {table}(concept_id,{column}) VALUES(?,?)',(ident,value))
        for value in entry['related_concepts']:
            target=db.execute('SELECT id FROM math_concepts WHERE canonical_name=?',(value,)).fetchone()[0]
            db.execute('INSERT INTO math_related_concepts(concept_id,related_canonical_name,related_concept_id) VALUES(?,?,?)',(ident,value,target))
        actual=read_snapshot(database,connection=db)[entry['canonical_name']]
        intended={k:sorted(v) if isinstance(v,list) else v for k,v in entry.items() if k!='canonical_name'}
        if actual!=intended:
            raise ValueError('Verification failed; insertion rolled back.')
        db.commit()
    print('Created:',entry['title'])
    print('Backup:',backup)
    return backup


def prepare(base, local, live, canonical, output):
    baseline=read_snapshot(base)
    working=read_snapshot(local)
    if canonical in baseline:
        raise ValueError('This entry exists in the baseline. Use the existing-entry workflow.')
    if canonical not in working:
        raise ValueError('Entry not found in local working database.')
    entry=dict(working[canonical],canonical_name=canonical)
    validate(entry)
    with closing(sqlite3.connect(live.resolve().as_uri()+'?mode=ro',uri=True)) as db:
        check_target(db,entry)
    output.mkdir(parents=True,exist_ok=False)
    (output/'entry.json').write_text(json.dumps(entry,ensure_ascii=False,indent=2),encoding='utf-8')
    for name in ('publish_math_entry.py','preview_math_sync.py'):
        shutil.copyfile(Path(__file__).with_name(name),output/name)
    (output/'REVIEW.txt').write_text('NEW ENTRY: '+entry['title']+'\nCanonical: '+canonical+'\nSlug: '+entry['slug']+'\nReview entry.json before applying. No existing entries will be overwritten.\n',encoding='utf-8')
    print('Prepared review folder:',output)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='action',required=True)
    prep=sub.add_parser('prepare')
    for arg in ('base','local','live','output'): prep.add_argument('--'+arg,type=Path,required=True)
    prep.add_argument('--canonical',required=True)
    execute=sub.add_parser('apply')
    execute.add_argument('entry',type=Path)
    execute.add_argument('--root',type=Path,default=Path.home()/'chi-portfolio')
    args=parser.parse_args()
    if args.action=='prepare': prepare(args.base,args.local,args.live,args.canonical,args.output)
    else: apply(args.root/'backend/portfolio.db',json.loads(args.entry.read_text(encoding='utf-8')),args.root.parent/'backups',args.root/'backend/src')
