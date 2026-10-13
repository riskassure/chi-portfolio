"""Conservative photo reconciliation and verified, additive media downloads."""
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess

from photo_sync import LIMIT, target_path

PHOTO_FIELDS = ('file_path', 'title', 'location_name', 'latitude', 'longitude',
                'is_currently_displayed')
DRAFT_SQL = """CREATE TABLE google_photo_drafts (
    digest TEXT PRIMARY KEY, title TEXT NOT NULL, location TEXT NOT NULL DEFAULT '',
    published_id INTEGER)"""


def photos(db):
    columns = {row[1] for row in db.execute('PRAGMA table_info(photography_catalog)')}
    if columns != {'image_id', *PHOTO_FIELDS, 'last_displayed_date', 'display_count'}:
        raise ValueError('Unrecognized gallery schema; review required.')
    rows = db.execute('SELECT image_id,' + ','.join(PHOTO_FIELDS) + ' FROM photography_catalog').fetchall()
    result = {}
    for row in rows:
        path = row[1]
        validate_path(path)
        if path in result:
            raise ValueError('Duplicate photo filename; review required.')
        result[path] = (row[0], tuple(row[1:]))
    return result


def validate_path(path):
    if not isinstance(path, str) or not re.fullmatch(r'images/photography/[A-Za-z0-9_-]+\.webp', path):
        raise ValueError('Unsupported photo path; review required.')


def drafts(db, catalog):
    if not db.execute("SELECT 1 FROM sqlite_master WHERE name='google_photo_drafts'").fetchone():
        return {}
    columns = [row[1] for row in db.execute('PRAGMA table_info(google_photo_drafts)')]
    if columns != ['digest', 'title', 'location', 'published_id']:
        raise ValueError('Unrecognized Google Photos draft schema; review required.')
    ids = {value[0]: path for path, value in catalog.items()}
    result = {}
    for digest, title, location, linked in db.execute('SELECT * FROM google_photo_drafts'):
        if linked is not None and linked not in ids:
            raise ValueError('A local photo draft has a missing gallery entry; review required.')
        result[digest] = (title, location, ids.get(linked))
    return result


def reconcile(baseline, local, live):
    """Do not discard local edits; IDs and rotation counters are not content."""
    b, w, r = (photos(db) for db in (baseline, local, live))
    drafts(baseline, b)  # Validate even if only the baseline has a draft table.
    blocked = []
    for path in b.keys() | w.keys() | r.keys():
        before, working, remote = (items.get(path, (None, None))[1] for items in (b, w, r))
        if working != before and working != remote:
            blocked.append(path)
    local_drafts = drafts(local, w)
    remote_drafts = drafts(live, r)
    # Draft image bytes live in a private local folder, not the public gallery.
    # Do not pretend we can import remote-only drafts without those private files.
    for digest, row in remote_drafts.items():
        if local_drafts.get(digest) != row:
            blocked.append('remote draft: ' + digest)
    remapped = []
    for digest, (title, location, path) in local_drafts.items():
        if path is not None and path not in r:
            blocked.append('draft gallery entry: ' + path)
        else:
            remapped.append((digest, title, location, r[path][0] if path else None))
    return dict(blocked=sorted(set(blocked)), paths=sorted(r), drafts=remapped)


def preserve_drafts(db, rows):
    if not rows:
        return
    if not db.execute("SELECT 1 FROM sqlite_master WHERE name='google_photo_drafts'").fetchone():
        db.execute(DRAFT_SQL)
    db.execute('DELETE FROM google_photo_drafts')
    db.executemany('INSERT INTO google_photo_drafts VALUES (?,?,?,?)', rows)
    db.commit()


# Only reads files within the account's gallery directory. No uploaded code or
# remote database edits; paths are validated again on the server.
MANIFEST_SCRIPT = r'''
import hashlib,json,re,sys
from pathlib import Path
request=json.load(sys.stdin)
username=request['username']
assert re.fullmatch(r'[A-Za-z0-9_]+',username)
root=Path('/home')/username/'chi-portfolio/frontend'
root=root.resolve()
result={}
for path in request['paths']:
    assert re.fullmatch(r'images/photography/[A-Za-z0-9_-]+\.webp',path)
    target=root/path
    assert target.resolve()==target and target.is_file() and not target.is_symlink()
    size=target.stat().st_size
    assert 12 <= size <= 25*1024*1024
    data=target.read_bytes()
    assert len(data)==size and data[:4]==b'RIFF' and data[8:12]==b'WEBP'
    result[path]={'sha256':hashlib.sha256(data).hexdigest(),'size':size}
print('PHOTO_MANIFEST='+json.dumps(result))
'''


def remote_manifest(username, paths):
    if not re.fullmatch(r'[A-Za-z0-9_]+', username):
        raise ValueError('Invalid account username.')
    for path in paths:
        validate_path(path)
    result = subprocess.run(
        ['ssh', username+'@ssh.pythonanywhere.com', 'python3.13 -I -B -c '+shlex.quote(MANIFEST_SCRIPT)],
        input=json.dumps(dict(username=username, paths=paths)), text=True,
        stdout=subprocess.PIPE, check=True)
    lines = [line for line in result.stdout.splitlines() if line.startswith('PHOTO_MANIFEST=')]
    if len(lines) != 1:
        raise ValueError('Server did not return a photo manifest.')
    return json.loads(lines[0].split('=', 1)[1])


def check_file(path, entry):
    if not path.is_file() or path.stat().st_size != entry['size']:
        raise ValueError('Missing or different photo file: '+str(path))
    data = path.read_bytes()
    if data[:4] != b'RIFF' or data[8:12] != b'WEBP' or hashlib.sha256(data).hexdigest() != entry['sha256']:
        raise ValueError('Photo checksum mismatch: '+str(path))


def stage_media(username, paths, frontend, folder):
    """Download missing images privately; never overwrite a local image."""
    manifest = remote_manifest(username, paths)
    if not isinstance(manifest, dict) or set(manifest) != set(paths):
        raise ValueError('Photo manifest does not match the snapshot catalog.')
    staged = []
    total = 0
    for path in paths:
        entry = manifest[path]
        if (not isinstance(entry, dict) or type(entry.get('size')) is not int
                or not 12 <= entry['size'] <= LIMIT
                or not isinstance(entry.get('sha256'), str)
                or not re.fullmatch('[a-f0-9]{64}', entry['sha256'])):
            raise ValueError('Invalid photo manifest entry.')
        total += entry['size']
        if total > 1024*1024*1024:
            raise ValueError('Gallery exceeds the 1 GB synchronization limit; review required.')
    for index, path in enumerate(paths):
        target = target_path(frontend, {'photo': {'file_path': path}})
        entry = manifest[path]
        if target.exists():
            check_file(target, entry)
        else:
            temporary = folder / ('photo-'+str(index)+'.partial')
            remote = f'{username}@ssh.pythonanywhere.com:/home/{username}/chi-portfolio/frontend/{path}'
            subprocess.run(['scp', remote, str(temporary)], check=True)
            check_file(temporary, entry)
            staged.append((path, temporary))
    (folder/'photo-manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    return manifest, staged


def install_media(frontend, manifest, staged):
    for path, temporary in staged:
        target = target_path(frontend, {'photo': {'file_path': path}})
        target.parent.mkdir(parents=True, exist_ok=True)
        check_file(temporary, manifest[path])
        try:
            os.link(temporary, target)  # Atomic creation; no overwrite on a race.
        except FileExistsError:
            check_file(target, manifest[path])
        temporary.unlink()
    for path, entry in manifest.items():
        check_file(target_path(frontend, {'photo': {'file_path': path}}), entry)
