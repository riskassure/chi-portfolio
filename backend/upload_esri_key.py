"""Install the browser-scoped Esri key over SSH without logging its value."""
from pathlib import Path
import re
import shlex
import subprocess


REMOTE_SCRIPT = r'''
import os, sys, tempfile
from pathlib import Path
key = sys.stdin.buffer.read(8193)
if not key or len(key) > 8192 or any(chr(c).isspace() for c in key):
    raise ValueError('Invalid key')
folder = Path.home()
for part in ('.config', 'chi-portfolio'):
    folder = folder / part
    if folder.is_symlink():
        raise ValueError('Configuration directory is a link')
    folder.mkdir(mode=0o700, exist_ok=True)
target = folder / 'esri-api-key.txt'
if target.is_symlink() or (target.exists() and not target.is_file()):
    raise ValueError('Configuration target is not a regular file')
fd, temporary = tempfile.mkstemp(prefix='.esri-', dir=folder)
try:
    with os.fdopen(fd, 'wb') as stream:
        stream.write(key)
        stream.flush()
        os.fsync(stream.fileno())
    if Path(temporary).read_bytes() != key:
        raise ValueError('Upload verification failed')
    os.chmod(temporary, 0o600)
    os.replace(temporary, target)
    if target.read_bytes() != key:
        raise ValueError('Installed key verification failed')
    print('ESRI_KEY_INSTALLED')
finally:
    if os.path.exists(temporary):
        os.unlink(temporary)
'''


def upload(username, path=None, *, interactive=True):
    if not isinstance(username, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*', username):
        raise ValueError('Invalid hosting username.')
    path = Path(path) if path else Path.home() / '.config/chi-portfolio/esri-api-key.txt'
    try:
        with path.open('rb') as stream:
            raw = stream.read(16385)
        if len(raw) > 16384:
            raise ValueError()
        key = raw.decode('utf-8-sig').strip()
        if not key or len(key.encode('utf-8')) > 8192 or any(c.isspace() for c in key):
            raise ValueError()
    except (OSError, UnicodeError, ValueError):
        raise ValueError('Save a valid Esri key in ~/.config/chi-portfolio/esri-api-key.txt first.') from None
    command = ['ssh']
    if not interactive:
        command += ['-o', 'BatchMode=yes']
    command += ['-o', 'ConnectTimeout=15', username + '@ssh.pythonanywhere.com',
                'python3.13 -I -B -c ' + shlex.quote(REMOTE_SCRIPT)]
    try:
        result = subprocess.run(command, input=key.encode('utf-8'), stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, timeout=120)
    except (OSError, subprocess.TimeoutExpired):
        raise ValueError('Key upload did not finish. Check SSH access and retry option 17.') from None
    if result.returncode or b'ESRI_KEY_INSTALLED' not in result.stdout.splitlines():
        raise ValueError('Key upload could not be verified. Check SSH access and retry option 17.')
    return 'Esri key uploaded and verified at /home/' + username + '/.config/chi-portfolio/esri-api-key.txt (owner access only).'
