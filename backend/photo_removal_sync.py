"""Remove a reviewed gallery entry, retaining the image and a database backup."""
from contextlib import closing
import io
import json
from pathlib import Path
import re
import sqlite3
import uuid
import zipfile

from photo_sync import catalog
from photo_metadata_sync import FIELDS, metadata, validate_details, image_hash


def validate(payload):
    if not isinstance(payload, dict) or set(payload) != {'kind', 'file_path', 'expected', 'sha256'} or payload['kind'] != 'photo-remove':
        raise ValueError('Invalid photo removal package.')
    if not isinstance(payload['file_path'], str) or not re.fullmatch(r'images/photography/[A-Za-z0-9_-]+\.webp', payload['file_path']):
        raise ValueError('Unsupported photo filename.')
    if not isinstance(payload['sha256'], str) or not re.fullmatch('[a-f0-9]{64}', payload['sha256']):
        raise ValueError('Invalid image checksum.')
    validate_details(payload['expected'])


def unpack(data, payload):
    validate(payload)
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        if archive.namelist() != ['photo-remove.json']:
            raise ValueError('Photo removal packages contain only photo-remove.json.')


def prepare(base, working, file_path, frontend, output):
    before, after = catalog(base).get(file_path), catalog(working).get(file_path)
    if before is None or after is None:
        raise ValueError('Select an existing photo present in both baseline and working gallery.')
    if metadata(before) != metadata(after):
        raise ValueError('This photo has unpublished local edits. Resolve those before preparing removal.')
    payload = dict(kind='photo-remove', file_path=file_path, expected=metadata(before),
                   sha256=image_hash(frontend, file_path))
    validate(payload)
    with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('photo-remove.json', json.dumps(payload, indent=2))
    return payload


def status(database, payload, frontend, connection=None):
    validate(payload)
    try:
        if image_hash(frontend, payload['file_path']) != payload['sha256']:
            return 'CONFLICT - image differs from the reviewed local image'
    except FileNotFoundError:
        return 'CONFLICT - retained image is missing; review required'
    if connection is None:
        with closing(sqlite3.connect(Path(database).resolve().as_uri()+'?mode=ro', uri=True)) as db:
            db.execute('BEGIN')
            return status(database, payload, frontend, db)
    rows = connection.execute('SELECT '+','.join(FIELDS)+' FROM photography_catalog WHERE file_path=?', (payload['file_path'],)).fetchall()
    if not rows:
        return 'ALREADY PRESENT - requested gallery removal already complete; image retained'
    if len(rows) == 1 and dict(zip(FIELDS, rows[0])) == payload['expected']:
        return 'EXPECTED TEXT MATCHES - gallery removal eligible for publication; image retained'
    return 'CONFLICT - photo details changed since the baseline'


def apply(database, payload, backups, frontend):
    validate(payload)
    with closing(sqlite3.connect(Path(database).resolve().as_uri()+'?mode=rw', uri=True, timeout=10)) as db:
        db.execute('PRAGMA foreign_keys=ON')
        db.execute('BEGIN IMMEDIATE')
        outcome = status(database, payload, frontend, db)
        if outcome.startswith('ALREADY PRESENT'):
            return dict(status='ALREADY_PRESENT', canonical=payload['file_path'], backup=None)
        if not outcome.startswith('EXPECTED TEXT MATCHES'):
            raise ValueError(outcome)
        has_drafts = db.execute("SELECT 1 FROM sqlite_master WHERE name='google_photo_drafts'").fetchone()
        if has_drafts and [row[1] for row in db.execute('PRAGMA table_info(google_photo_drafts)')] != ['digest', 'title', 'location', 'published_id']:
            raise ValueError('Unrecognized photo draft schema; removal stopped.')
        backups = Path(backups)
        backups.mkdir(parents=True, exist_ok=True)
        backup = backups/('before-photo-removal-'+uuid.uuid4().hex+'.db')
        with backup.open('xb'):
            pass
        with closing(sqlite3.connect(Path(database).resolve().as_uri()+'?mode=ro', uri=True)) as source, closing(sqlite3.connect(backup)) as dest:
            source.backup(dest)
            if dest.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                raise ValueError('Photo backup verification failed.')
        image_id = db.execute('SELECT image_id FROM photography_catalog WHERE file_path=?', (payload['file_path'],)).fetchone()[0]
        if has_drafts:
            db.execute('UPDATE google_photo_drafts SET published_id=NULL WHERE published_id=?', (image_id,))
        db.execute('DELETE FROM photography_catalog WHERE image_id=?', (image_id,))
        if not status(database, payload, frontend, db).startswith('ALREADY PRESENT') or db.execute('PRAGMA foreign_key_check').fetchone():
            raise ValueError('Photo removal verification failed.')
        db.commit()
    return dict(status='APPLIED', canonical=payload['file_path'], backup=str(backup))
