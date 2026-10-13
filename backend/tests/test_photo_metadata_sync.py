from contextlib import closing
import copy
import hashlib
from io import BytesIO
import json
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from PIL import Image
from flask import Flask
import photo_metadata_sync as edits
from inspect_staged_package import preview
from live_math_publication import publish
import website_workflow as helper
from routes import admin_photography


class PhotoMetadataTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.front = self.root/'frontend'
        self.db = self.root/'backend'/'portfolio.db'
        self.db.parent.mkdir()
        self.path = 'images/photography/aspen.webp'
        target = self.front/self.path
        target.parent.mkdir(parents=True)
        buffer = BytesIO()
        Image.new('RGB', (10, 10), 'green').save(buffer, 'WEBP')
        self.image = buffer.getvalue()
        target.write_bytes(self.image)
        with closing(sqlite3.connect(self.db)) as db:
            db.executescript('''CREATE TABLE photography_catalog(
                image_id INTEGER PRIMARY KEY, file_path TEXT UNIQUE, title TEXT, location_name TEXT,
                latitude REAL, longitude REAL, is_currently_displayed INTEGER,
                last_displayed_date TEXT, display_count INTEGER);''')
            db.execute('INSERT INTO photography_catalog VALUES(17,?,?,?,?,?,0,?,23)',
                       (self.path, 'Aspen', 'June Lake', 0, 0, 'yesterday'))
            db.commit()
        self.working = self.root/'working.db'
        shutil.copyfile(self.db, self.working)
        self.sql(self.working, "UPDATE photography_catalog SET title='Aspen forest',location_name='June Lake Loop',latitude=37.8,longitude=-119.1")
        self.package = self.root/'package.zip'
        self.payload = edits.prepare(self.db, self.working, self.path, self.front, self.package)

    def sql(self, path, query):
        with closing(sqlite3.connect(path)) as db:
            db.execute(query)
            db.commit()

    def row(self, path):
        with closing(sqlite3.connect(path)) as db:
            return db.execute('SELECT * FROM photography_catalog').fetchone()

    def apply(self):
        return edits.apply(self.db, self.payload, self.root/'backups', self.front)

    def test_review_dispatch_backup_preserves_image_ids_and_rotation(self):
        report = preview(self.package.read_bytes())
        self.assertIn('Before: "Aspen"', report)
        self.assertIn('After: "Aspen forest"', report)
        before = self.row(self.db)
        result = publish(self.package.read_bytes(), self.db, self.root/'backups', self.db.parent/'src')
        self.assertEqual(result['status'], 'APPLIED')
        self.assertEqual(self.row(result['backup']), before)
        after = self.row(self.db)
        self.assertEqual(after[:2], before[:2])
        self.assertEqual(after[6:], before[6:])
        self.assertEqual(after[2:6], ('Aspen forest', 'June Lake Loop', 37.8, -119.1))
        self.assertEqual((self.front/self.path).read_bytes(), self.image)
        self.assertEqual(self.apply()['status'], 'ALREADY_PRESENT')
        self.assertEqual(len(list((self.root/'backups').iterdir())), 1)

    def test_newer_remote_edit_after_preflight_is_not_overwritten(self):
        self.assertTrue(edits.status(self.db, self.payload, self.front).startswith('EXPECTED TEXT MATCHES'))
        self.sql(self.db, "UPDATE photography_catalog SET title='Road edit'")
        with self.assertRaisesRegex(ValueError, 'CONFLICT'):
            self.apply()
        self.assertEqual(self.row(self.db)[2], 'Road edit')
        self.assertFalse((self.root/'backups').exists())

    def test_rotation_changes_do_not_block_or_get_overwritten(self):
        self.sql(self.db, 'UPDATE photography_catalog SET is_currently_displayed=1,display_count=45')
        self.apply()
        self.assertEqual(self.row(self.db)[6:], (1, 'yesterday', 45))

    def test_missing_or_changed_image_blocks(self):
        target = self.front/self.path
        for data in (b'different', None):
            if data is None:
                target.unlink()
            else:
                target.write_bytes(data)
            with self.assertRaisesRegex(ValueError, 'CONFLICT'):
                self.apply()
        self.assertEqual(self.row(self.db)[2], 'Aspen')

    def test_deleted_photo_blocks(self):
        self.sql(self.db, 'DELETE FROM photography_catalog')
        with self.assertRaisesRegex(ValueError, 'CONFLICT'):
            self.apply()

    def test_failed_verification_rolls_back_update(self):
        self.sql(self.db, "CREATE TRIGGER alter_title AFTER UPDATE ON photography_catalog BEGIN UPDATE photography_catalog SET title='Unexpected' WHERE image_id=NEW.image_id; END")
        with self.assertRaisesRegex(ValueError, 'verification failed'):
            self.apply()
        self.assertEqual(self.row(self.db)[2], 'Aspen')

    def test_unsupported_fields_paths_and_nonfinite_coordinates_rejected(self):
        for key, value in [('file_path', '../secret.webp'), ('sha256', 'bad')]:
            payload = dict(self.payload, **{key: value})
            with self.assertRaises(ValueError):
                edits.validate(payload)
        for key, value in [('latitude', float('nan')), ('longitude', 181), ('title', ''), ('display_count', 12)]:
            payload = copy.deepcopy(self.payload)
            payload['replacement'][key] = value
            with self.assertRaises(ValueError):
                edits.validate(payload)

    def test_extra_archive_file_is_rejected(self):
        with zipfile.ZipFile(self.package, 'a') as archive:
            archive.writestr('extra.py', 'print("not allowed")')
        with self.assertRaises(ValueError):
            preview(self.package.read_bytes())

    def test_helper_rejects_edits_after_review_and_ignores_rotation(self):
        state = dict(base=str(self.db), working=str(self.working), username='cwoo',
                     base_sha256=hashlib.sha256(self.db.read_bytes()).hexdigest())
        with patch.object(helper, 'ROOT', self.root), patch.object(helper, 'save'):
            helper.prepare_photo_edit(state, self.path)
            self.sql(self.working, 'UPDATE photography_catalog SET display_count=100,is_currently_displayed=1')
            self.assertEqual(helper.current_job(state)['kind'], 'photo-edit')
            self.sql(self.working, "UPDATE photography_catalog SET title='Another edit'")
            with self.assertRaises(ValueError):
                helper.current_job(state)

    def test_admin_editor_validates_and_supports_older_clients(self):
        app = Flask(__name__)
        app.secret_key = 'test'
        app.register_blueprint(admin_photography.photography_bp)
        client = app.test_client()
        body = dict(image_id=17, title='Edited title', location_name='Lake', latitude=37, longitude=-119)
        with patch.object(admin_photography, 'DB_PATH', self.db):
            self.assertEqual(client.post('/api/photography/update', json=body).status_code, 403)
            with client.session_transaction() as session:
                session['is_admin'] = True
            self.assertEqual(client.post('/api/photography/update', json=body).status_code, 200)
            self.assertEqual(self.row(self.db)[2], 'Edited title')
            for field, value in [('latitude', 'NaN'), ('longitude', 181), ('title', ''), ('location_name', [])]:
                self.assertEqual(client.post('/api/photography/update', json=dict(body, **{field: value})).status_code, 400)
            self.assertEqual(client.post('/api/photography/update', json=dict(body, image_id=999)).status_code, 404)
            del body['title']
            self.assertEqual(client.post('/api/photography/update', json=body).status_code, 200)
            self.assertEqual(self.row(self.db)[2], 'Edited title')
