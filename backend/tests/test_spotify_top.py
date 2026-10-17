from contextlib import closing
from datetime import datetime, timezone, timedelta
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from services.music import spotify_top
from services.music.music_catalog import read_catalog, tables
from services.music.spotify_api import SpotifyApiError


class SpotifyTopTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        root = Path(temp.name); self.catalog = root / 'catalog.db'
        with closing(sqlite3.connect(self.catalog)) as db, db:
            db.execute('CREATE TABLE music_catalog (id INTEGER PRIMARY KEY, track_id TEXT, track_name TEXT, composer TEXT, spotify_playlist TEXT)')
            db.execute('INSERT INTO music_catalog VALUES (1,?,?,?,?)', ('a'*22, 'Curated title', 'Composer', 'Old playlist'))
            tables(db)
            db.execute('INSERT INTO music_overrides VALUES (?,?,?)', ('a'*22, 'performer', 'Edited performer'))
        patcher = patch.object(spotify_top, 'job_path', return_value=root/'jobs.db')
        patcher.start(); self.addCleanup(patcher.stop)
        self.now = datetime(2026, 10, 16, tzinfo=timezone.utc)
        self.tracks = [dict(id=c*22, name='Spotify title '+c, artists=[{'name':'Artist'}],
                            album={'name':'Album'}, duration_ms=120000) for c in ('b','a')]
        self.api = Mock(); self.api.get.return_value = {'items': self.tracks}

    def test_daily_refresh_preserves_order_edits_and_no_fake_counts(self):
        result = spotify_top.run(self.catalog, api=self.api, now=self.now)
        self.assertEqual(result['status'], 'ok')
        catalog = read_catalog(self.catalog)
        self.assertEqual(catalog['ranking']['source'], 'spotify_top')
        self.assertEqual([r['track_id'] for r in catalog['data']], ['b'*22,'a'*22])
        self.assertIsNone(catalog['data'][0]['plays'])
        self.assertEqual(catalog['data'][1]['track_name'], 'Curated title')
        self.assertEqual(catalog['data'][1]['performer'], 'Edited performer')
        spotify_top.run(self.catalog, api=self.api, now=self.now+timedelta(hours=23))
        self.api.get.assert_called_once()
        spotify_top.run(self.catalog, api=self.api, now=self.now+timedelta(days=1))
        self.assertEqual(self.api.get.call_count, 2)
        with closing(sqlite3.connect(self.catalog)) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM music_catalog').fetchone()[0], 1)

    def test_empty_and_malformed_result_preserve_last_catalog(self):
        spotify_top.run(self.catalog, api=self.api, now=self.now)
        previous = read_catalog(self.catalog)
        for i, items in enumerate([[], [{'id':'bad'}], self.tracks*2, None]):
            self.api.get.return_value = {'items':items}
            result = spotify_top.run(self.catalog, api=self.api, force=True, now=self.now+timedelta(days=i+1))
            self.assertEqual(result['status'], 'error')
            self.assertEqual(read_catalog(self.catalog), previous)

    def test_rate_limit_and_missing_database(self):
        self.api.get.side_effect = SpotifyApiError(429, 7200)
        self.assertEqual(spotify_top.run(self.catalog, api=self.api, now=self.now)['status'], 'error')
        self.assertEqual(spotify_top.run(self.catalog, api=self.api, force=True, now=self.now+timedelta(hours=1))['status'], 'waiting')
        self.api.get.assert_called_once()
        missing = self.catalog.parent/'missing.db'
        self.assertEqual(spotify_top.run(missing, api=self.api)['status'], 'error')
        self.assertFalse(missing.exists())


if __name__ == '__main__': unittest.main()
