from contextlib import closing
from datetime import datetime, timezone, timedelta
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from services.music.music_catalog import publish, read_catalog
from services.music.spotify_history import import_history
from services.music.spotify_jobs import run_job
from services.music.spotify_jobs import run_local_job
from services.music.spotify_auth import SpotifyError
from services.music.spotify_api import SpotifyApi, SpotifyApiError
from services.music.spotify_sync import collect_recent, connect, sync_playlists


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.catalog = self.root / "catalog.db"
        self.history = self.root / "history.db"
        self.now = datetime(2026, 9, 10, tzinfo=timezone.utc)
        with closing(sqlite3.connect(self.catalog)) as db, db:
            db.execute("CREATE TABLE music_catalog (id INTEGER PRIMARY KEY, track_id TEXT, track_name TEXT, composer TEXT, spotify_playlist TEXT)")
            db.executemany("INSERT INTO music_catalog VALUES (?, ?, ?, ?, ?)",
                           [(i, str(i) * 22, 'Curated name', 'Curated composer', 'Old') for i in range(1, 27)])
        archive = self.root / "export.zip"
        with zipfile.ZipFile(archive, "w") as z:
            z.writestr('Streaming_History_Audio_2026.json', json.dumps([
                {"spotify_track_uri": "spotify:track:" + "a" * 22, "ms_played": 30000, "ts": '2026-09-01T00:00:00Z'},
                {"spotify_track_uri": "spotify:track:" + "a" * 22, "ms_played": 30000, "ts": '2026-09-02T00:00:00Z'},
                {"spotify_track_uri": "spotify:track:" + "b" * 22, "ms_played": 29999, "ts": '2026-09-02T00:00:00Z'}]))
        import_history(archive, self.history)
        self.candidates = {letter * 22: {"track": {"id": letter * 22, "name": "Name " + letter,
                                                "artists": [{"name": "Artist"}], "duration_ms": 60000},
                                            "playlists": {"A", "B"}, "aliases": {letter * 22}}
                           for letter in 'abcdefghijklmnopqrstuvwxyz1'}

    def test_ranking_cap_global_filter_pagination_and_preserved_metadata(self):
        meta = publish(self.catalog, self.history, self.candidates, {}, self.now)
        self.assertEqual(meta['target_count'], 26)
        page = read_catalog(self.catalog)
        self.assertEqual(len(page['data']), 25)
        self.assertEqual(page['total_pages'], 2)
        self.assertEqual(page['data'][0]['track_id'], 'a' * 22)
        self.assertEqual(page['data'][0]['plays'], 2)
        second = read_catalog(self.catalog, page=2)
        self.assertEqual(len(second['data']), 1)
        self.assertFalse({r['track_id'] for r in page['data']} & {r['track_id'] for r in second['data']})
        filtered = read_catalog(self.catalog, search=second['data'][0]['track_name'])
        self.assertEqual(filtered['total_records'], 1)
        self.assertEqual(read_catalog(self.catalog, playlist='B')['total_records'], 26)
        curated = read_catalog(self.catalog, search='Curated composer')['data'][0]
        self.assertEqual(curated['composer'], 'Curated composer')
        self.assertEqual(read_catalog(self.catalog, search='nothing')['total_records'], 0)

    def test_failed_publication_keeps_previous_and_overrides_survive(self):
        publish(self.catalog, self.history, self.candidates, {}, self.now)
        before = read_catalog(self.catalog)
        with self.assertRaises(KeyError):
            publish(self.catalog, self.history, {'bad': {}}, {}, self.now)
        self.assertEqual(read_catalog(self.catalog), before)
        with closing(sqlite3.connect(self.catalog)) as db, db:
            db.execute('INSERT INTO music_overrides VALUES (?, ?, ?)', ('a'*22, 'track_name', 'My title'))
        publish(self.catalog, self.history, self.candidates, {}, self.now)
        self.assertEqual(read_catalog(self.catalog)['data'][0]['track_name'], 'My title')

    def test_recent_collection_is_repeatable_and_never_adds_verified_plays(self):
        class Api:
            def items(self, url):
                return [{"track": {"id": 'b'*22}, 'played_at': '2026-09-03T00:00:00Z'}]
        self.assertEqual(collect_recent(Api(), self.history), 1)
        self.assertEqual(collect_recent(Api(), self.history), 0)
        publish(self.catalog, self.history, self.candidates, {}, self.now)
        self.assertEqual(read_catalog(self.catalog, search='Name b')['data'][0]['plays'], 0)

    def test_job_weekly_due_and_rate_limit_backoff(self):
        with patch('services.music.spotify_jobs.collect_recent', return_value=0), patch(
                'services.music.spotify_jobs.sync_playlists', return_value=(self.candidates, {})) as sync:
            self.assertEqual(run_job(self.catalog, self.history, None, self.now)['status'], 'ok')
            run_job(self.catalog, self.history, None, self.now)
            self.assertEqual(sync.call_count, 1)
        with patch('services.music.spotify_jobs.collect_recent', side_effect=SpotifyApiError(429, 7200)) as collect:
            self.assertEqual(run_job(self.catalog, self.history, None, self.now, force=True)['status'], 'error')
            self.assertEqual(run_job(self.catalog, self.history, None, self.now, force=True)['status'], 'waiting')
            self.assertEqual(collect.call_count, 1)

    def test_playlist_cache_and_multiple_memberships(self):
        class Api:
            calls = 0
            def items(self, url):
                if url.startswith('/me/'):
                    return [{'id': x*22, 'name': x, 'snapshot_id': 'one'} for x in 'xy']
                self.calls += 1
                return [{'item': {'id': 'a'*22, 'type': 'track', 'name': 'Song'}}]
            def get(self, url):
                return {'snapshot_id': 'one'}
        api = Api()
        tracks, _ = sync_playlists(api, self.history)
        self.assertEqual(tracks['a'*22]['playlists'], {'x', 'y'})
        sync_playlists(api, self.history)
        self.assertEqual(api.calls, 2)

    def test_missed_weekly_run_catches_up_on_next_invocation(self):
        with patch('services.music.spotify_jobs.collect_recent', return_value=0), patch(
                'services.music.spotify_jobs.sync_playlists', return_value=(self.candidates, {})) as sync:
            run_job(self.catalog, self.history, None, self.now)
            returned = self.now + timedelta(days=9)
            result = run_job(self.catalog, self.history, None, returned)
            self.assertIn('publication', result)
            self.assertEqual(sync.call_count, 2)
            # Another invocation after sign-in does not publish twice.
            run_job(self.catalog, self.history, None, returned + timedelta(minutes=15))
            self.assertEqual(sync.call_count, 2)

    def test_offline_logon_retries_without_losing_due_update(self):
        with patch('services.music.spotify_jobs.collect_recent', side_effect=SpotifyError('Network unavailable')):
            self.assertEqual(run_job(self.catalog, self.history, None, self.now)['status'], 'error')
        with patch('services.music.spotify_jobs.collect_recent', return_value=0), patch(
                'services.music.spotify_jobs.sync_playlists', return_value=(self.candidates, {})):
            result = run_job(self.catalog, self.history, None, self.now + timedelta(minutes=5))
            self.assertIn('publication', result)

    def test_manual_update_bypasses_weekly_interval(self):
        with patch('services.music.spotify_jobs.collect_recent', return_value=0), patch(
                'services.music.spotify_jobs.sync_playlists', return_value=(self.candidates, {})) as sync:
            run_job(self.catalog, self.history, None, self.now)
            self.assertIn('publication', run_job(self.catalog, self.history, None, self.now, force=True))
            self.assertEqual(sync.call_count, 2)

    def test_manual_and_scheduled_jobs_share_lock(self):
        with closing(sqlite3.connect(self.root / 'spotify-job-lock.db')) as db:
            db.execute('BEGIN IMMEDIATE')
            with patch('services.music.spotify_jobs.token_path', return_value=self.root/'tokens.json'), patch(
                    'services.music.spotify_jobs.run_job') as run:
                self.assertEqual(run_local_job(force=True)['status'], 'busy')
                run.assert_not_called()

    def test_pagination_rejects_external_urls_before_reading_token(self):
        with patch('services.music.spotify_api.SpotifyAuth') as auth:
            api = SpotifyApi(auth())
            with self.assertRaises(Exception):
                api.get('https://example.com/v1/anything')
            auth().access_token.assert_not_called()


if __name__ == '__main__':
    unittest.main()
