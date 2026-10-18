"""Publishable gallery preferences, separate from each database's rotation state."""
import hashlib
import json
from pathlib import Path
from services.file_persistence import exclusive_edit, replace_text

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
    def check_revision():
        if read()[1] != revision:
            raise Conflict('Gallery settings changed. Reload before saving.')

    with exclusive_edit(target, Conflict, 'Another gallery edit is in progress. Reload and try again.'):
        check_revision()
        content = PREFIX + json.dumps(settings, indent=2) + ';\n'
        replace_text(target, content, prefix='.gallery-', before_replace=check_revision)
