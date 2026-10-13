"""Review and publish metadata edits without changing images or rotation state."""
from contextlib import closing
import hashlib
import io
import json
import math
from pathlib import Path
import re
import sqlite3
import uuid
import zipfile

from photo_sync import catalog, target_path

FIELDS = ('title', 'location_name', 'latitude', 'longitude')


def metadata(photo):
    return {key: photo[key] for key in FIELDS}


def validate(payload):
    if not isinstance(payload, dict) or set(payload) != {'kind', 'file_path', 'expected', 'replacement', 'sha256'} or payload['kind'] != 'photo-edit':
        raise ValueError('Invalid photo metadata package.')
    if not isinstance(payload['file_path'], str) or not re.fullmatch(r'images/photography/[A-Za-z0-9_-]+\.webp', payload['file_path']):
        raise ValueError('Unsupported photo filename.')
    if not isinstance(payload['sha256'], str) or not re.fullmatch('[a-f0-9]{64}', payload['sha256']):
        raise ValueError('Invalid image checksum.')
    for name in ('expected', 'replacement'):
        row = payload[name]
        if not isinstance(row, dict) or set(row) != set(FIELDS):
            raise ValueError('Only title, location and coordinates can be edited.')
        for key in FIELDS:
            value = row[key]
            # Older gallery rows may have unset location/coordinates. Preserve
            # these exactly rather than changing unrelated fields implicitly.
            if value is None and key != 'title':
                continue
            if key in ('title', 'location_name'):
                if not isinstance(value, str) or len(value) > 200 or (key == 'title' and not value.strip()):
                    raise ValueError('Invalid photo title or location.')
            elif type(value) not in (int, float) or not math.isfinite(value) or abs(value) > (90 if key == 'latitude' else 180):
                raise ValueError('Invalid photo coordinates.')
    if payload['expected'] == payload['replacement']:
        raise ValueError('No photo metadata changes to publish.')


def unpack(data, payload):
    validate(payload)
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        if archive.namelist() != ['photo-edit.json']:
            raise ValueError('Photo metadata packages contain only photo-edit.json.')


def image_hash(frontend, file_path):
    if not isinstance(file_path, str) or not re.fullmatch(r'images/photography/[A-Za-z0-9_-]+\.webp', file_path):
        raise ValueError('Unsupported photo filename.')
    target = target_path(frontend, {'photo': {'file_path': file_path}})
    return hashlib.sha256(target.read_bytes()).hexdigest()


def prepare(base, working, file_path, frontend, output):
    before, after = catalog(base).get(file_path), catalog(working).get(file_path)
    if before is None or after is None:
        raise ValueError('Select a photo present in both the baseline and local gallery.')
    payload = dict(kind='photo-edit', file_path=file_path, expected=metadata(before),
                   replacement=metadata(after), sha256=image_hash(frontend, file_path))
    validate(payload)
    with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('photo-edit.json', json.dumps(payload, indent=2))
    return payload


def status(database, payload, frontend, connection=None):
    validate(payload)
    try:
        if image_hash(frontend, payload['file_path']) != payload['sha256']:
            return 'CONFLICT - image differs from the reviewed local image'
    except FileNotFoundError:
        return 'CONFLICT - gallery image is missing'
    if connection is None:
        with closing(sqlite3.connect(Path(database).resolve().as_uri()+'?mode=ro', uri=True)) as db:
            db.execute('BEGIN')
            return status(database, payload, frontend, db)
    rows = connection.execute('SELECT '+','.join(FIELDS)+' FROM photography_catalog WHERE file_path=?', (payload['file_path'],)).fetchall()
    if len(rows) != 1:
        return 'CONFLICT - expected exactly one existing gallery entry'
    current = dict(zip(FIELDS, rows[0]))
    if current == payload['replacement']:
        return 'ALREADY PRESENT - photo metadata matches'
    if current == payload['expected']:
        return 'EXPECTED TEXT MATCHES - photo metadata eligible for publication'
    return 'CONFLICT - photo metadata changed since the baseline'


def apply(database, payload, backups, frontend):
    validate(payload)
    with closing(sqlite3.connect(Path(database).resolve().as_uri()+'?mode=rw', uri=True, timeout=10)) as db:
        db.execute('BEGIN IMMEDIATE')
        outcome = status(database, payload, frontend, db)
        if outcome.startswith('ALREADY PRESENT'):
            return dict(status='ALREADY_PRESENT', canonical=payload['file_path'], backup=None)
        if not outcome.startswith('EXPECTED TEXT MATCHES'):
            raise ValueError(outcome)
        backups = Path(backups)
        backups.mkdir(parents=True, exist_ok=True)
        backup = backups/('before-photo-metadata-update-'+uuid.uuid4().hex+'.db')
        with backup.open('xb'):
            pass
        with closing(sqlite3.connect(Path(database).resolve().as_uri()+'?mode=ro', uri=True)) as source, closing(sqlite3.connect(backup)) as dest:
            source.backup(dest)
            if dest.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                raise ValueError('Photo backup verification failed.')
        db.execute('UPDATE photography_catalog SET '+','.join(key+'=?' for key in FIELDS)+' WHERE file_path=?',
                   tuple(payload['replacement'][key] for key in FIELDS)+(payload['file_path'],))
        if not status(database, payload, frontend, db).startswith('ALREADY PRESENT'):
            raise ValueError('Photo metadata verification failed.')
        db.commit()
    return dict(status='APPLIED', canonical=payload['file_path'], backup=str(backup))
