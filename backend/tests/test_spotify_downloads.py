from contextlib import closing
from datetime import datetime, timezone, timedelta
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from services.music.spotify_downloads import import_downloads
from services.music.spotify_jobs import run_job
from services.music.spotify_auth import SpotifyError
from services.music.spotify_sync import connect


class DownloadsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.history = self.folder / 'history.db'
        self.now = datetime.now(timezone.utc)

    def archive(self, name='my_spotify_data.zip', records=None):
        path = self.folder / name
        if records is None:
            records = [{'spotify_track_uri': 'spotify:track:'+'a'*22, 'ts': '2026-09-01T00:00:00Z', 'ms_played': 40000}]
        with zipfile.ZipFile(path, 'w') as z:
            z.writestr('Spotify/Streaming_History_Audio_2026.json', json.dumps(records))
            z.writestr('private.json', '{"ip":"not imported"}')
        os.utime(path, (self.now.timestamp()-120,)*2)
        return path

    def test_remembers_contents_even_when_archive_is_renamed(self):
        path = self.archive()
        original = path.read_bytes()
        first = import_downloads(self.folder, self.history)
        self.assertEqual(first['imported'], 1)
        self.assertEqual(path.read_bytes(), original)
        self.assertEqual(import_downloads(self.folder, self.history)['already_processed'], 1)
        path.rename(self.folder/'spotify_copy.zip')
        self.assertEqual(import_downloads(self.folder, self.history)['already_processed'], 1)
        self.assertFalse((self.folder/'private.json').exists())

    def test_waits_for_recent_and_partial_downloads(self):
        path = self.archive()
        os.utime(path, (self.now.timestamp(),)*2)
        self.assertEqual(import_downloads(self.folder, self.history, self.now.timestamp())['deferred'], 1)
        os.utime(path, (self.now.timestamp()-120,)*2)
        Path(str(path)+'.crdownload').touch()
        self.assertEqual(import_downloads(self.folder, self.history)['deferred'], 1)

    def test_invalid_archive_rolls_back_and_can_be_replaced(self):
        self.archive(records=[{'spotify_track_uri':'spotify:track:'+'a'*22,'ts':'bad','ms_played':40000}])
        self.assertTrue(import_downloads(self.folder, self.history)['issues'])
        with closing(sqlite3.connect(self.history)) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM history_archives').fetchone()[0], 0)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM spotify_history').fetchone()[0], 0)
        self.archive()
        self.assertEqual(import_downloads(self.folder, self.history)['imported'], 1)

    def test_ignores_unrelated_zip_and_overlapping_events(self):
        self.archive('holiday.zip')
        self.assertEqual(import_downloads(self.folder, self.history)['imported'], 0)
        self.archive()
        import_downloads(self.folder, self.history)
        self.archive(records=[{'spotify_track_uri':'spotify:track:'+'a'*22,'ts':'2026-09-01T00:00:00Z','ms_played':40000},
                              {'spotify_track_uri':'spotify:track:'+'a'*22,'ts':'2026-09-02T00:00:00Z','ms_played':40000}])
        self.assertEqual(import_downloads(self.folder, self.history)['imported'], 1)
        with closing(sqlite3.connect(self.history)) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM spotify_history').fetchone()[0], 2)

    def test_new_archive_forces_refresh_and_survives_network_failure(self):
        self.archive()
        with closing(connect(self.history)) as db, db:
            db.execute("INSERT INTO sync_state VALUES ('last_publication', ?)",(str(self.now.timestamp()),))
        with patch('services.music.spotify_jobs.collect_recent', side_effect=SpotifyError('Offline')):
            result=run_job(None,self.history,None,self.now,downloads=self.folder)
            self.assertEqual(result['archive_import']['imported'],1)
        with patch('services.music.spotify_jobs.collect_recent', return_value=0), patch(
                'services.music.spotify_jobs.sync_playlists', return_value=({},{})), patch(
                'services.music.spotify_jobs.publish', return_value={'ok':True}) as publish:
            result=run_job(None,self.history,None,self.now+timedelta(minutes=5),downloads=self.folder)
            self.assertIn('publication',result)
            publish.assert_called_once()
        with closing(sqlite3.connect(self.history)) as db:
            self.assertEqual(db.execute("SELECT value FROM sync_state WHERE key='history_publication_pending'").fetchone()[0],'0')


if __name__ == '__main__':
    unittest.main()
