from contextlib import closing
import json
from io import BytesIO
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from PIL import Image
from flask import Flask
from routes.google_photos import google_photos_bp
from services.photography import google_photos_import as service

class ImportTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        for name, value in [('DB_PATH', root / 'test.db'), ('DRAFT_ROOT', root / 'private'), ('PHOTO_TARGET_DIR', root / 'public')]:
            mock = patch.object(service, name, value)
            mock.start()
            self.addCleanup(mock.stop)
        with closing(sqlite3.connect(service.DB_PATH)) as db, db:
            db.execute('CREATE TABLE photography_catalog (image_id INTEGER PRIMARY KEY,file_path TEXT,title TEXT,location_name TEXT,latitude REAL,longitude REAL,is_currently_displayed INTEGER,display_count INTEGER)')
        output = BytesIO()
        Image.new('RGB', (20, 10), 'red').save(output, 'JPEG')
        self.image = output.getvalue()
        self.item = {'id':'photo', 'type':'PHOTO', 'mediaFile': {'baseUrl':'https://lh3.googleusercontent.com/test', 'filename':'Landscape.jpg'}}

    def test_import_private_duplicate_and_publish_idempotent(self):
        with patch.object(service, 'fetch', return_value=self.image):
            self.assertTrue(service.import_item(self.item, 'token')['imported'])
            self.assertTrue(service.import_item(self.item, 'token')['duplicate'])
        self.assertFalse(service.PHOTO_TARGET_DIR.exists())
        with closing(sqlite3.connect(service.DB_PATH)) as db, db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM photography_catalog').fetchone()[0], 0)
        draft = service.drafts()[0]
        first = service.publish(draft['digest'], 'A title', 'A location')
        self.assertEqual(service.publish(draft['digest'], 'Other', 'Other'), first)
        self.assertEqual(service.drafts(), [])
        with closing(sqlite3.connect(service.DB_PATH)) as db, db:
            self.assertEqual(db.execute('SELECT title,is_currently_displayed FROM photography_catalog').fetchall(), [('A title', 1)])
        self.assertEqual(len(list(service.PHOTO_TARGET_DIR.glob('*.webp'))), 1)

    def test_bad_content_urls_and_video(self):
        with patch.object(service, 'fetch') as fetch:
            self.assertTrue(service.import_item({'type':'VIDEO'}, 'token')['skipped'])
            self.item['mediaFile']['baseUrl'] = 'https://evil.example/photo'
            with self.assertRaises(service.GooglePhotosError):
                service.import_item(self.item, 'token')
            fetch.assert_not_called()
        self.item['mediaFile']['baseUrl'] = 'https://lh3.googleusercontent.com/test'
        with patch.object(service, 'fetch', return_value=b'not an image'):
            with self.assertRaises(service.GooglePhotosError):
                service.import_item(self.item, 'token')
        self.assertEqual(service.drafts(), [])

    def test_pagination(self):
        with patch.object(service, 'api', side_effect=[{'mediaItems':[self.item], 'nextPageToken':'next'}, {'mediaItems':[{'id':'second'}]}]) as api:
            self.assertEqual(len(service.picked_items('session', 'token')), 2)
            self.assertIn('pageToken=next', api.call_args.args[0])

    def test_routes_gate_and_import_only_picked_ids(self):
        app = Flask(__name__, template_folder=str(Path(__file__).resolve().parents[1] / 'src/templates'))
        app.secret_key = 'test'
        app.register_blueprint(google_photos_bp)
        client = app.test_client()
        base = 'http://127.0.0.1:5000'
        prefix = '/api/photography/google'
        self.assertEqual(client.get(prefix+'/drafts', base_url=base).status_code, 403)
        with client.session_transaction(base_url=base) as session:
            session['is_admin'] = True
            session['google_photos_csrf'] = 'csrf'
            session['google_picker_id'] = 'picker'
        self.assertEqual(client.post(prefix+'/picker', base_url=base).status_code, 400)
        with patch('routes.google_photos.auth.access_token', return_value='token'), patch.object(service, 'picked_items', return_value=[self.item]), patch.object(service, 'import_item') as save:
            response = client.post(prefix+'/picker/import', base_url=base, data={'csrf':'csrf','id':'not-selected'})
            self.assertEqual(response.status_code, 400)
            save.assert_not_called()
        self.assertEqual(client.get(prefix+'/manage', base_url=base).status_code, 200)

if __name__ == '__main__':
    unittest.main()
