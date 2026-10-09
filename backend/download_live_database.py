"""Download a verified PythonAnywhere SQLite snapshot via interactive SSH/SCP."""
import argparse
import base64
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shlex
import shutil
import sqlite3
import subprocess
import uuid


def verify(path, expected_hash):
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != expected_hash:
        raise ValueError('Downloaded file does not match the server snapshot checksum.')
    with closing(sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True)) as db:
        if db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise ValueError('Downloaded database failed integrity check.')
        if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='math_concepts'").fetchone():
            raise ValueError('Snapshot is not a portfolio database.')


def download(destination, username='cwoo'):
    if not re.fullmatch(r'[A-Za-z0-9_]+', username):
        raise ValueError('Invalid PythonAnywhere username.')
    for tool in ('ssh', 'scp'):
        if not shutil.which(tool):
            raise RuntimeError(f'{tool} is required. Install Windows OpenSSH Client.')
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
    folder = destination.expanduser().resolve()/stamp
    folder.mkdir(parents=True, exist_ok=False)
    remote = f'/home/{username}/backups/portfolio-{stamp}.db'
    source = f'/home/{username}/chi-portfolio/backend/portfolio.db'
    script = f'''
from pathlib import Path
from contextlib import closing
import sqlite3, hashlib, os
os.umask(0o077)
source=Path({source!r})
target=Path({remote!r})
target.parent.mkdir(parents=True,exist_ok=True)
with target.open('xb'): pass
with closing(sqlite3.connect(source.as_uri()+'?mode=ro',uri=True)) as src:
    with closing(sqlite3.connect(target)) as dst:
        src.backup(dst)
        if dst.execute('PRAGMA integrity_check').fetchone()[0]!='ok':
            raise RuntimeError('Live snapshot failed integrity check')
print('SNAPSHOT_SHA256='+hashlib.sha256(target.read_bytes()).hexdigest())
'''
    encoded = base64.b64encode(script.encode()).decode()
    command = 'python3.13 -c '+shlex.quote(f"import base64; exec(base64.b64decode('{encoded}'))")
    host = username+'@ssh.pythonanywhere.com'
    print('Creating a consistent live snapshot. SSH may ask for your PythonAnywhere account password.',flush=True)
    result = subprocess.run(['ssh',host,command],stdout=subprocess.PIPE,text=True,check=True)
    match = re.search(r'^SNAPSHOT_SHA256=([a-f0-9]{64})$', result.stdout,re.MULTILINE)
    if not match:
        raise RuntimeError('Server did not return a snapshot checksum. Download cancelled.')
    partial = folder/'download.partial'
    print('Downloading snapshot. You may be asked for the account password again.',flush=True)
    subprocess.run(['scp',host+':'+remote, str(partial)],check=True)
    verify(partial,match[1])
    final = folder/'live-snapshot.db'
    partial.rename(final)
    (folder/'snapshot.json').write_text(json.dumps(dict(
        downloaded_utc=datetime.now(timezone.utc).isoformat(),
        source=source, remote_backup=remote, host=host,
        sha256=match[1], local_file=final.name),indent=2),encoding='utf-8')
    print(f'Verified database saved to: {final}')
    print('Keep this snapshot unchanged. The working local database was not replaced.')
    print(f'Server backup retained at: {remote}')
    return final


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination',type=Path,default=Path.home()/'Downloads'/'chi-portfolio'/'database')
    parser.add_argument('--username',default='cwoo')
    args = parser.parse_args()
    try:
        download(args.destination,args.username)
    except (OSError,ValueError,RuntimeError,sqlite3.Error,subprocess.CalledProcessError) as error:
        raise SystemExit(f'Download failed: {error}. Any .partial file is not a verified backup.')
