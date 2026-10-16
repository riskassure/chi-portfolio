from contextlib import closing
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch
from flask import Flask

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from services import gallery_settings
from routes import admin_photography

ORIGIN = 'http://127.0.0.1:5001'


class GallerySettingsTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.settings = self.root / 'settings.js'
        self.settings.write_text(gallery_settings.PREFIX + '{"photo_count":12};\n')
        self.db = self.root / 'photos.db'
        with closing(sqlite3.connect(self.db)) as conn:
            conn.execute('CREATE TABLE photography_catalog(image_id,file_path,title,location_name,latitude,longitude,is_currently_displayed,display_count,last_displayed_date)')
            conn.executemany('INSERT INTO photography_catalog VALUES(?,?,?,?,?,?,?,?,?)',
                [(i, f'images/photography/{i}.webp', str(i), 'Place', 1, 2, int(i < 3), 0, None) for i in range(18)])
            conn.commit()
        for patcher in [patch.object(gallery_settings, 'path', return_value=self.settings),
                        patch.object(admin_photography, 'DB_PATH', self.db),
                        patch.dict(os.environ, {'FLASK_ENV': 'development', 'PORTFOLIO_LOCAL_PORT': '5001'})]:
            patcher.start(); self.addCleanup(patcher.stop)
        app = Flask(__name__); app.secret_key = 'test'; app.register_blueprint(admin_photography.photography_bp)
        self.client = app.test_client()

    def login(self):
        with self.client.session_transaction(base_url=ORIGIN) as session: session['is_admin'] = True

    def post(self, count=6, revision=None):
        return self.client.post('/api/photography/settings', base_url=ORIGIN, headers={'Origin': ORIGIN},
            json={'settings': {'photo_count': count}, 'revision': revision or gallery_settings.read()[1]})

    def test_count_applies_without_changing_database(self):
        before = self.db.read_bytes()
        self.assertEqual(self.client.get('/api/photography/current').json['count'], 12)
        self.login()
        self.assertEqual(self.post().status_code, 200)
        self.assertEqual(self.client.get('/api/photography/current').json['count'], 6)
        self.assertEqual(self.db.read_bytes(), before)
        self.assertEqual(self.client.get('/api/photography/settings').json['settings']['photo_count'], 6)
        # A stale browser cannot reset rotation to its old default of three.
        rotated = self.client.post('/api/photography/rotate', json={'limit': 3})
        self.assertEqual(rotated.json['count'], 6)

    def test_access_validation_and_conflict(self):
        self.assertEqual(self.post().status_code, 403)
        self.login()
        revision = gallery_settings.read()[1]
        self.assertEqual(self.post().status_code, 200)
        self.assertEqual(self.post(9, revision).status_code, 409)
        for value in (0, 18, True, '12'):
            self.assertEqual(self.post(value).status_code, 400)
        with patch.dict(os.environ, {'FLASK_ENV': 'production'}):
            self.assertEqual(self.post().status_code, 403)

    def test_failed_write_keeps_settings(self):
        self.login(); before = self.settings.read_bytes()
        with patch.object(gallery_settings.os, 'replace', side_effect=OSError()):
            self.assertEqual(self.post().status_code, 503)
        self.assertEqual(self.settings.read_bytes(), before)
        self.assertFalse(self.settings.with_suffix('.lock').exists())


if __name__ == '__main__':
    unittest.main()
