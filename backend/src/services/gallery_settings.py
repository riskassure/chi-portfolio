"""Publishable gallery preferences, separate from each database's rotation state."""
import hashlib
import json
import os
from pathlib import Path
import tempfile

PREFIX = 'window.GALLERY_SETTINGS = '


def path():
    return Path(__file__).resolve().parents[3] / 'frontend/photography/gallery-settings.js'


def read():
    raw = path().read_bytes()
    text = raw.decode('utf-8').strip()
    if not text.startswith(PREFIX) or not text.endswith(';'):
        raise ValueError('Invalid gallery settings.')
    settings = json.loads(text[len(PREFIX):-1])
    validate(settings)
    return settings, hashlib.sha256(raw).hexdigest()


def validate(settings):
    if (not isinstance(settings, dict) or set(settings) != {'photo_count'}
            or type(settings['photo_count']) is not int or settings['photo_count'] not in (3, 6, 9, 12)):
        raise ValueError('Choose 3, 6, 9, or 12 photos.')


class Conflict(ValueError):
    pass


def save(settings, revision):
    validate(settings)
    target = path()
    lock = target.with_suffix('.lock')
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise Conflict('Another gallery edit is in progress. Reload and try again.') from None
    os.close(fd)
    temporary = None
    try:
        if read()[1] != revision:
            raise Conflict('Gallery settings changed. Reload before saving.')
        fd, temporary = tempfile.mkstemp(prefix='.gallery-', suffix='.tmp', dir=target.parent)
        with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as stream:
            stream.write(PREFIX + json.dumps(settings, indent=2) + ';\n')
            stream.flush()
            os.fsync(stream.fileno())
        if read()[1] != revision:
            raise Conflict('Gallery settings changed. Reload before saving.')
        os.replace(temporary, target)
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)
        lock.unlink()
