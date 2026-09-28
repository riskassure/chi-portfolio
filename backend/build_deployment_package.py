"""Build a private, allowlisted first-deployment ZIP with a SQLite snapshot."""
import argparse
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]

def build(destination, code_only=False):
    files = set()
    for p in (ROOT / 'frontend').rglob('*'):
        if p.is_file() and (not code_only or 'images' not in p.relative_to(ROOT/'frontend').parts) and p.suffix.lower() in {'.html','.js','.css','.jpg','.jpeg','.png','.webp','.gif','.svg','.ico','.woff','.woff2'}:
            files.add(p)
    for tree in ['backend/src', 'backend/tests']:
        files.update(p for p in (ROOT/tree).rglob('*.py') if '__pycache__' not in p.parts)
    files.update(p for p in (ROOT/'backend/src/templates').rglob('*.html'))
    files.update(p for p in (ROOT/'backend/data/math/diagrams').rglob('*')
                 if not code_only
                 if p.is_file() and p.suffix.lower() in {'.svg','.png','.jpg','.jpeg','.gif','.webp'})
    for name in ['backend/requirements.txt','backend/serve.py','backend/backup_database.py',
                 'backend/pythonanywhere_wsgi.py','backend/setup_pythonanywhere.py',
                 'backend/backup_site.py', 'PYTHONANYWHERE.md', 'UPDATING_WEBSITE.md']:
        files.add(ROOT/name)
    with tempfile.TemporaryDirectory() as temp:
        snapshot=Path(temp)/'portfolio.db'
        if not code_only:
          with closing(sqlite3.connect((ROOT/'backend/portfolio.db').as_uri()+'?mode=ro',uri=True)) as src:
            with closing(sqlite3.connect(snapshot)) as dst:
                src.backup(dst)
                # Only the copy is sanitized. Keep schemas, omit import staging and unpublished drafts.
                names={r[0] for r in dst.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                for table in ['stg_spotify_import','stg_math_import','google_photo_drafts','spotify_history']:
                    if table in names:dst.execute('DELETE FROM "'+table+'"')
                dst.commit()
                dst.execute('VACUUM')
                assert dst.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
                assert not dst.execute('PRAGMA foreign_key_check').fetchall()
        entries={p.relative_to(ROOT).as_posix():p for p in sorted(files)}
        if not code_only:
            entries['backend/portfolio.db']=snapshot
        manifest={'created_utc':datetime.now(timezone.utc).isoformat(), 'kind':'code-update' if code_only else 'first-deployment', 'files':{}}
        destination.parent.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(destination,'x',compression=zipfile.ZIP_DEFLATED) as archive:
            for name,path in entries.items():
                content=path.read_bytes()
                manifest['files'][name]={'bytes':len(content),'sha256':hashlib.sha256(content).hexdigest()}
                archive.writestr('chi-portfolio/'+name,content)
            archive.writestr('chi-portfolio/manifest.json',json.dumps(manifest,indent=2))
        with zipfile.ZipFile(destination) as archive:assert archive.testzip() is None
        print(f'Built {destination.name}: {len(entries)} files, {destination.stat().st_size/1024/1024:.1f} MiB ZIP, '
              f'{sum(v["bytes"] for v in manifest["files"].values())/1024/1024:.1f} MiB extracted.')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'dist/chi-portfolio-pythonanywhere.zip')
    parser.add_argument('--code-only',action='store_true',help='Exclude database and managed media for routine code updates.')
    args=parser.parse_args()
    if args.code_only and args.output==ROOT/'dist/chi-portfolio-pythonanywhere.zip':
        args.output=ROOT/'dist/chi-portfolio-code-update.zip'
    build(args.output,args.code_only)
