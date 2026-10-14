"""Review and publish selected UTF-8 frontend files with conflict checks and backups."""
import difflib
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shlex
import stat
import subprocess
import tempfile
import uuid
import zipfile

FILE_LIMIT = 2 * 1024 * 1024
TOTAL_LIMIT = 10 * 1024 * 1024
MAX_FILES = 20


def validate_path(name):
    if not isinstance(name, str) or not re.fullmatch(r'(?:[A-Za-z0-9_-]+/)*[A-Za-z0-9_-]+\.(?:html|css|js)', name):
        raise ValueError('Use a relative frontend HTML, CSS or JS path, without links or hidden directories.')


def target_path(frontend, name):
    validate_path(name)
    root = Path(frontend).resolve()
    target = root/name
    if target.is_symlink() or target.resolve() != target or not target.resolve().is_relative_to(root):
        raise ValueError('Frontend paths cannot traverse links or leave frontend.')
    return target


def read_text(frontend, name):
    path = target_path(frontend, name)
    if not path.exists():
        return None
    with path.open('rb') as stream:
        data = stream.read(FILE_LIMIT+1)
    if len(data) > FILE_LIMIT or b'\x00' in data:
        raise ValueError('Frontend files must be text and no larger than 2 MB.')
    try:
        return data.decode('utf-8')
    except UnicodeError:
        raise ValueError('Frontend files must use UTF-8 encoding.') from None


def checksum(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest() if text is not None else None


def validate(payload):
    if not isinstance(payload, dict) or set(payload) != {'kind', 'files'} or payload['kind'] != 'frontend-files':
        raise ValueError('Invalid frontend package.')
    files = payload['files']
    if not isinstance(files, list) or not 1 <= len(files) <= MAX_FILES:
        raise ValueError('Select between 1 and 20 frontend files.')
    seen, total = set(), 0
    for item in files:
        if not isinstance(item, dict) or set(item) != {'path', 'expected', 'replacement'}:
            raise ValueError('Invalid frontend file entry.')
        validate_path(item['path'])
        if item['path'].casefold() in seen:
            raise ValueError('Duplicate frontend path.')
        seen.add(item['path'].casefold())
        for field in ('expected', 'replacement'):
            value = item[field]
            if value is None and field == 'expected':
                continue
            if not isinstance(value, str) or '\x00' in value:
                raise ValueError('Frontend packages contain UTF-8 text, not deletions or binary files.')
            size = len(value.encode('utf-8'))
            if size > FILE_LIMIT:
                raise ValueError('Frontend file exceeds 2 MB.')
            total += size
        if item['expected'] == item['replacement']:
            raise ValueError('Package contains an unchanged file.')
    if total > TOTAL_LIMIT:
        raise ValueError('Frontend review exceeds 10 MB.')


def unpack(data, payload):
    validate(payload)
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        if archive.namelist() != ['frontend-files.json']:
            raise ValueError('Frontend packages contain only frontend-files.json.')


def review(payload):
    validate(payload)
    lines = ['Proposed operation: publish frontend HTML/CSS/JavaScript',
             'Review every difference: the expected version was read from live during preparation.',
             'No database changes, Python changes or website reload are included.',
             'Multiple files are replaced individually; a brief mixed-version interval is possible.']
    for item in payload['files']:
        name = item['path']
        lines += ['File: frontend/'+name, 'Expected SHA-256: '+str(checksum(item['expected'])),
                  'Proposed SHA-256: '+checksum(item['replacement'])]
        lines += list(difflib.unified_diff((item['expected'] or '').splitlines(), item['replacement'].splitlines(),
                                         fromfile='live/'+name, tofile='local/'+name, lineterm=''))
        if item['expected'] is None:
            lines.append('New file: the live path must remain absent until publication.')
        elif item['expected'].splitlines() == item['replacement'].splitlines():
            lines.append('Only line endings or the final newline changed; checksums above show the exact bytes.')
    return '\n'.join(lines)


def status(payload, frontend):
    validate(payload)
    matches = []
    for item in payload['files']:
        current = read_text(frontend, item['path'])
        if current not in (item['expected'], item['replacement']):
            return 'CONFLICT - live file changed: '+item['path']
        matches.append(current == item['replacement'])
    return ('ALREADY PRESENT - all frontend files match' if all(matches) else
            'EXPECTED TEXT MATCHES - frontend files eligible for publication')


def capture_live(username, paths):
    if not re.fullmatch(r'[A-Za-z0-9_]+', username):
        raise ValueError('Invalid account username.')
    if not 1 <= len(paths) <= MAX_FILES or len({path.casefold() for path in paths}) != len(paths):
        raise ValueError('Select 1 to 20 distinct frontend files.')
    for path in paths:
        validate_path(path)
    # Send only this trusted local reader, never the HTML/JS being reviewed.
    script = "import json,sys; config=json.load(sys.stdin); scope={}; exec(compile(config['reader'],'<frontend-reader>','exec'),scope); result={p:scope['read_text'](config['frontend'],p) for p in config['paths']}; print('FRONTEND_SNAPSHOT='+json.dumps(result))"
    request = dict(reader=Path(__file__).read_text(encoding='utf-8'), paths=paths,
                   frontend=f'/home/{username}/chi-portfolio/frontend')
    result = subprocess.run(['ssh', username+'@ssh.pythonanywhere.com', 'python3.13 -I -B -c '+shlex.quote(script)],
                            input=json.dumps(request), text=True, encoding='utf-8', stdout=subprocess.PIPE, check=True)
    lines = [line.split('=', 1)[1] for line in result.stdout.splitlines() if line.startswith('FRONTEND_SNAPSHOT=')]
    if len(lines) != 1:
        raise ValueError('No unambiguous live file snapshot received.')
    snapshot = json.loads(lines[0])
    if not isinstance(snapshot, dict) or set(snapshot) != set(paths):
        raise ValueError('Live file snapshot does not match the selected paths.')
    return snapshot


def prepare(frontend, paths, live, output):
    if set(paths) != set(live):
        raise ValueError('Live snapshot does not match selected files.')
    files = []
    for path in paths:
        replacement = read_text(frontend, path)
        if replacement is None:
            raise ValueError('Selected local file is missing: '+path)
        if replacement != live[path]:
            files.append(dict(path=path, expected=live[path], replacement=replacement))
    if not files:
        raise ValueError('Selected files already match live. No package needed.')
    payload = dict(kind='frontend-files', files=files)
    validate(payload)
    with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('frontend-files.json', json.dumps(payload, ensure_ascii=False, indent=2))
    return payload


def temporary_file(target, text, mode):
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.frontend-', dir=target.parent)
    path = Path(name)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(text.encode('utf-8'))
            stream.flush()
            os.fsync(stream.fileno())
        path.chmod(mode)
        return path
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def apply(payload, frontend, backups):
    validate(payload)
    backups = Path(backups)
    backups.mkdir(parents=True, exist_ok=True)
    lock = backups/'.frontend-publish.lock'
    try:
        lock.mkdir()
    except FileExistsError:
        raise ValueError('Frontend publication is locked. Check an active or interrupted publication before retrying.') from None
    keep_lock, staged, installed = False, [], []
    backup = None
    journal = None
    try:
        outcome = status(payload, frontend)
        if outcome.startswith('ALREADY PRESENT'):
            return dict(status='ALREADY_PRESENT', canonical='Frontend files', backup=None)
        if not outcome.startswith('EXPECTED TEXT MATCHES'):
            raise ValueError(outcome)
        backup = backups/('before-frontend-update-'+uuid.uuid4().hex)
        backup.mkdir()
        (lock/'backup.txt').write_text(str(backup), encoding='utf-8')
        journal = dict(status='PREPARING', files=[])
        for index, item in enumerate(payload['files']):
            path = item['path']
            target = target_path(frontend, path)
            current = read_text(frontend, path)
            if current == item['replacement']:
                continue
            if current != item['expected']:
                raise ValueError('Live file changed before backup: '+path)
            mode = stat.S_IMODE(target.stat().st_mode) if current is not None else 0o644
            if current is not None:
                saved = backup/(str(index)+'.before')
                saved.write_bytes(current.encode('utf-8'))
                if saved.read_bytes() != current.encode('utf-8'):
                    raise ValueError('Frontend backup verification failed.')
            record = dict(path=path, before=index if current is not None else None,
                          expected_sha256=checksum(current), replacement_sha256=checksum(item['replacement']), mode=mode)
            journal['files'].append(record)
            staged.append((item, current, mode, temporary_file(target, item['replacement'], mode)))
        journal['status'] = 'PREPARED'
        (backup/'manifest.json').write_text(json.dumps(journal, indent=2), encoding='utf-8')
        # All backups and temporary files exist before the first replacement.
        for item, current, mode, temporary in staged:
            target = target_path(frontend, item['path'])
            if read_text(frontend, item['path']) != current:
                raise ValueError('Live file changed before replacement: '+item['path'])
            if current is None:
                os.link(temporary, target)  # Refuse a concurrently created file.
            else:
                os.replace(temporary, target)
            installed.append((item, current, mode))
            if read_text(frontend, item['path']) != item['replacement']:
                raise ValueError('Published file verification failed.')
        if not status(payload, frontend).startswith('ALREADY PRESENT'):
            raise ValueError('Frontend batch verification failed.')
        journal['status'] = 'APPLIED'
        (backup/'manifest.json').write_text(json.dumps(journal, indent=2), encoding='utf-8')
        return dict(status='APPLIED', canonical='Frontend files', backup=str(backup))
    except BaseException as error:
        failures = []
        for item, current, mode in reversed(installed):
            restore = None
            try:
                target = target_path(frontend, item['path'])
                if read_text(frontend, item['path']) != item['replacement']:
                    raise ValueError('Concurrent edit; automatic restoration refused.')
                if current is None:
                    target.unlink()
                else:
                    restore = temporary_file(target, current, mode)
                    os.replace(restore, target)
                if read_text(frontend, item['path']) != current:
                    raise ValueError('Restoration verification failed.')
            except BaseException:
                failures.append(item['path'])
            finally:
                if restore is not None:
                    restore.unlink(missing_ok=True)
        if failures:
            keep_lock = True
            raise RuntimeError(f'Frontend update needs manual recovery; publication remains locked. Backup: {backup}. Files: {failures}') from error
        if backup is not None and journal is not None:
            journal['status'] = 'ROLLED_BACK'
            (backup/'manifest.json').write_text(json.dumps(journal, indent=2), encoding='utf-8')
        raise
    finally:
        for _, _, _, temporary in staged:
            temporary.unlink(missing_ok=True)
        if not keep_lock:
            (lock/'backup.txt').unlink(missing_ok=True)
            lock.rmdir()
