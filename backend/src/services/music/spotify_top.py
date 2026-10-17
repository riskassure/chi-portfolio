"""Daily Spotify affinity ranking, preserving the last good catalog and edits."""
import argparse
from contextlib import closing
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sqlite3

from services.music.music_catalog import EDITABLE, tables
from services.music.spotify_api import SpotifyApi, SpotifyApiError
from services.music.spotify_auth import SpotifyError, token_path

TIME_RANGE = 'medium_term'
TRACK_LIMIT = 50
INTERVAL = 86400


def publish_top(catalog, tracks, now):
    if not isinstance(tracks, list) or not tracks or len(tracks) > TRACK_LIMIT:
        raise SpotifyError('Spotify returned no usable ranking. The previous catalog is retained.')
    seen = set()
    for track in tracks:
        if (not isinstance(track, dict) or not re.fullmatch(r'[A-Za-z0-9]{22}', track.get('id') or '')
                or track['id'] in seen or not isinstance(track.get('name'), str) or not track['name']):
            raise SpotifyError('Spotify returned an incomplete ranking. The previous catalog is retained.')
        seen.add(track['id'])
    with closing(sqlite3.connect(Path(catalog).resolve().as_uri() + '?mode=rw', uri=True, timeout=30)) as db, db:
        db.row_factory = sqlite3.Row
        originals = {r['track_id']: dict(r) for r in db.execute('SELECT * FROM music_catalog')}
        tables(db)
        rows = []
        for rank, track in enumerate(tracks, 1):
            album = track.get('album') or {}
            seconds = int(track.get('duration_ms', 0)) // 1000
            row = dict(track_id=track['id'], rank=rank, plays=None, popularity=None,
                       genre=None, composition_name=None, unit_name=None, composer=None,
                       track_name=track['name'], performer='; '.join(a['name'] for a in track.get('artists', [])),
                       album_name=album.get('name', ''), release_date=album.get('release_date', ''),
                       duration_string=f'{seconds // 60:02}:{seconds % 60:02}',
                       playlists=[], spotify_playlist='')
            original = originals.get(track['id'], {})
            for field in (*EDITABLE, 'unit_name'):
                if original.get(field) is not None:
                    row[field] = original[field]
            rows.append(row)
        meta = dict(source='spotify_top', time_range=TIME_RANGE, target_count=len(rows),
                    published_at=now.isoformat(), refresh_interval_hours=24,
                    ranking_description='Spotify ranking over approximately the last six months; not exact play counts.')
        # Replace only the derived view; original catalog and editorial overrides stay intact.
        db.execute('DELETE FROM music_publication')
        db.executemany('INSERT INTO music_publication VALUES (?,?,?)',
                       [(r['track_id'], r['rank'], json.dumps(r)) for r in rows])
        db.execute('DELETE FROM music_publication_meta')
        db.executemany('INSERT INTO music_publication_meta VALUES (?,?)',
                       [(k, json.dumps(v)) for k, v in meta.items()])
    return meta


def job_path():
    return token_path().parent / 'spotify-top-jobs.db'


def status(catalog):
    path = job_path()
    if not path.exists():
        return None
    with closing(sqlite3.connect(path.as_uri() + '?mode=ro', uri=True)) as db:
        row = db.execute('SELECT report FROM jobs WHERE catalog=?', (str(Path(catalog).resolve()),)).fetchone()
        return json.loads(row[0]) if row else None


def run(catalog, *, force=False, api=None, now=None):
    now = now or datetime.now(timezone.utc)
    catalog = Path(catalog).resolve()
    if not catalog.is_file():
        return {'status': 'error', 'message': 'Selected music database is missing.'}
    path = job_path(); path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(path, timeout=1)) as lock:
        lock.execute('CREATE TABLE IF NOT EXISTS jobs (catalog TEXT PRIMARY KEY, success REAL, retry REAL, report TEXT)')
        try:
            lock.execute('BEGIN IMMEDIATE')
        except sqlite3.OperationalError:
            return {'status': 'busy', 'message': 'A Spotify refresh is already running.'}
        row = lock.execute('SELECT success,retry,report FROM jobs WHERE catalog=?', (str(catalog),)).fetchone()
        success, retry = row[:2] if row else (0, 0)
        if retry > now.timestamp():
            return {'status': 'waiting', 'message': 'Waiting before retrying Spotify.',
                    'retry_at': datetime.fromtimestamp(retry, timezone.utc).isoformat()}
        if not force and success and now.timestamp() - success < INTERVAL:
            return {'status': 'ok', 'message': 'Daily refresh is not due yet.'}
        report = {'status': 'ok', 'checked_at': now.isoformat()}
        try:
            response = (api or SpotifyApi()).get(f'/me/top/tracks?time_range={TIME_RANGE}&limit={TRACK_LIMIT}&offset=0')
            report['publication'] = publish_top(catalog, response.get('items'), now)
            success, retry = now.timestamp(), 0
            report['message'] = f"Updated {report['publication']['target_count']} Spotify-ranked tracks."
        except (SpotifyError, OSError, sqlite3.Error, ValueError, KeyError, TypeError, AttributeError) as error:
            report['status'] = 'error'
            report['message'] = str(error) if isinstance(error, SpotifyError) else 'Refresh failed. The previous catalog is retained.'
            retry = now.timestamp() + (max(3600, error.retry_after) if isinstance(error, SpotifyApiError) else 300)
        lock.execute('INSERT OR REPLACE INTO jobs VALUES (?,?,?,?)', (str(catalog), success, retry, json.dumps(report)))
        lock.commit()
        return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', required=True, type=Path)
    parser.add_argument('--refresh', action='store_true')
    args = parser.parse_args()
    report = run(args.database, force=args.refresh)
    if __import__('sys').stdout is not None:
        print(json.dumps(report, indent=2))
    if report['status'] != 'ok':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
