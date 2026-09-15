"""Picker API access and private drafts; only published photos enter the gallery."""
from contextlib import closing
from hashlib import sha256
from io import BytesIO
import json
import sqlite3
from pathlib import Path
from urllib.parse import urlencode, urlparse
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError, URLError
from PIL import Image, ImageOps
from config import DB_PATH, PHOTO_TARGET_DIR
from services.photography.google_photos_auth import GooglePhotosError, token_path

DRAFT_ROOT = token_path().parent / 'google-photo-drafts'


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def fetch(url, token, method='GET', payload=None, binary=False):
    req = Request(url, data=json.dumps(payload).encode() if payload is not None else None,
                  headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'}, method=method)
    try:
        with build_opener(NoRedirect).open(req, timeout=30) as response:
            body = response.read(25 * 1024 * 1024 + 1)
            if len(body) > 25 * 1024 * 1024:
                raise GooglePhotosError('Photo is too large to import.')
            return body if binary else (json.loads(body) if body else {})
    except (HTTPError, URLError, TimeoutError, ValueError):
        raise GooglePhotosError('Google Photos could not complete the request. Retry, or reconnect if your authorization expired.') from None


def api(path, token, method='GET', payload=None):
    return fetch('https://photospicker.googleapis.com/v1/' + path, token, method, payload)


def picked_items(sid, token):
    result, page, seen = [], '', set()
    while True:
        data = api('mediaItems?' + urlencode({'sessionId': sid, 'pageSize': 100, 'pageToken': page}), token)
        result.extend(data.get('mediaItems', []))
        page = data.get('nextPageToken', '')
        if not page:
            return result
        if page in seen:
            raise GooglePhotosError('Google returned an invalid photo list. Start a new selection.')
        seen.add(page)


def database():
    db = sqlite3.connect(str(DB_PATH), timeout=30)
    db.row_factory = sqlite3.Row
    db.execute('''CREATE TABLE IF NOT EXISTS google_photo_drafts (
        digest TEXT PRIMARY KEY, title TEXT NOT NULL, location TEXT NOT NULL DEFAULT '',
        published_id INTEGER)''')
    db.commit()
    return db


def draft_dir():
    directory = DRAFT_ROOT
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def import_item(item, token):
    if item.get('type') != 'PHOTO':
        return {'skipped': True, 'message': 'Videos are not imported.'}
    media = item.get('mediaFile', {})
    url = media.get('baseUrl', '')
    parsed = urlparse(url)
    if parsed.scheme != 'https' or not (parsed.hostname or '').endswith('.googleusercontent.com') or parsed.username or parsed.port not in (None, 443):
        raise GooglePhotosError('Google returned an unsupported photo URL.')
    raw = fetch(url + '=w1920-h1920', token, binary=True)
    try:
        with Image.open(BytesIO(raw)) as original:
            photo = ImageOps.exif_transpose(original).convert('RGB')
            photo.thumbnail((1920, 1920), Image.Resampling.LANCZOS)
            output = BytesIO()
            photo.save(output, 'WEBP', quality=85)
            content = output.getvalue()
    except (OSError, ValueError, Image.DecompressionBombError):
        raise GooglePhotosError('This file could not be decoded as a photo.') from None
    digest = sha256(content).hexdigest()
    title = Path(media.get('filename', 'Untitled photo')).stem[:200] or 'Untitled photo'
    with closing(database()) as db, db:
        db.execute('BEGIN IMMEDIATE')
        if db.execute('SELECT 1 FROM google_photo_drafts WHERE digest=?', (digest,)).fetchone():
            return {'duplicate': True}
        (draft_dir() / (digest + '.webp')).write_bytes(content)
        db.execute('INSERT INTO google_photo_drafts(digest,title) VALUES (?,?)', (digest, title))
    return {'imported': True}


def drafts():
    with closing(database()) as db:
        return [dict(row) for row in db.execute('SELECT * FROM google_photo_drafts WHERE published_id IS NULL ORDER BY rowid DESC')]


def publish(digest, title, location):
    with closing(database()) as db, db:
        db.execute('BEGIN IMMEDIATE')
        row = db.execute('SELECT * FROM google_photo_drafts WHERE digest=?', (digest,)).fetchone()
        if not row:
            raise GooglePhotosError('Photo not found. Refresh the review list.')
        if row['published_id']:
            return row['published_id']
        source = draft_dir() / (digest + '.webp')
        PHOTO_TARGET_DIR.mkdir(parents=True, exist_ok=True)
        target = PHOTO_TARGET_DIR / ('google-' + digest + '.webp')
        target.write_bytes(source.read_bytes())
        cursor = db.execute('''INSERT INTO photography_catalog
            (file_path,title,location_name,latitude,longitude,is_currently_displayed,display_count)
            VALUES (?,?,?,0,0,1,0)''', ('images/photography/' + target.name, title[:200] or row['title'], location[:200] or 'Unknown Location'))
        db.execute('UPDATE google_photo_drafts SET published_id=?,title=?,location=? WHERE digest=?',
                   (cursor.lastrowid, title[:200] or row['title'], location[:200], digest))
        return cursor.lastrowid
