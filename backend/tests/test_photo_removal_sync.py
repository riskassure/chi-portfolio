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
from PIL import Image
import photo_removal_sync as removal
import website_workflow as helper
import photo_home
from bring_changes_home import refresh
from inspect_staged_package import preview
from live_math_publication import publish


class PhotoRemovalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.front = self.root/'frontend'
        self.live = self.root/'backend'/'portfolio.db'
        self.live.parent.mkdir()
        self.path = 'images/photography/aspen.webp'
        target = self.front/self.path
        target.parent.mkdir(parents=True)
        buf = BytesIO()
        Image.new('RGB', (10, 10), 'green').save(buf, 'WEBP')
        self.image = buf.getvalue()
        target.write_bytes(self.image)
        with closing(sqlite3.connect(self.live)) as db:
            db.executescript('''
                CREATE TABLE math_concepts(id INTEGER PRIMARY KEY, content TEXT);
                CREATE TABLE photography_catalog(image_id INTEGER PRIMARY KEY, file_path TEXT UNIQUE,
                    title TEXT, location_name TEXT, latitude REAL, longitude REAL,
                    is_currently_displayed INTEGER, last_displayed_date TEXT, display_count INTEGER);
            ''')
            db.execute(photo_home.DRAFT_SQL)
            db.execute('INSERT INTO photography_catalog VALUES(17,?,?,?,?,?,1,NULL,23)',
                       (self.path, 'Aspen', 'June Lake Loop, CA', 0, 0))
            db.execute('INSERT INTO google_photo_drafts VALUES(?,?,?,17)', ('a'*64, 'Aspen', 'June Lake Loop'))
            db.commit()
        self.base, self.working = self.root/'base.db', self.root/'working.db'
        for path in (self.base, self.working):
            shutil.copyfile(self.live, path)
        self.package = self.root/'package.zip'
        self.payload = removal.prepare(self.base, self.working, self.path, self.front, self.package)
        self.state = dict(base=str(self.base), working=str(self.working), username='cwoo',
                          base_sha256=hashlib.sha256(self.base.read_bytes()).hexdigest(), job=None)

    def sql(self, query, database=None):
        with closing(sqlite3.connect(database or self.live)) as db:
            db.execute(query)
            db.commit()

    def rows(self, database, table):
        with closing(sqlite3.connect(database)) as db:
            return db.execute('SELECT * FROM '+table).fetchall()

    def apply(self):
        return removal.apply(self.live, self.payload, self.root/'backups', self.front)

    def test_prepare_is_read_only_and_review_explicit(self):
        self.assertEqual(self.base.read_bytes(), self.working.read_bytes())
        self.assertEqual(len(self.rows(self.live, 'photography_catalog')), 1)
        report = preview(self.package.read_bytes())
        self.assertIn('REMOVE one gallery entry', report)
        self.assertIn('direct URL', report)

    def test_dispatch_backup_removal_and_repeat_preserve_image_and_draft(self):
        before = self.rows(self.live, 'photography_catalog')
        result = publish(self.package.read_bytes(), self.live, self.root/'backups', self.live.parent/'src')
        self.assertEqual(result['status'], 'APPLIED')
        self.assertEqual(self.rows(result['backup'], 'photography_catalog'), before)
        self.assertEqual(self.rows(self.live, 'photography_catalog'), [])
        self.assertEqual(self.rows(self.live, 'google_photo_drafts'), [('a'*64, 'Aspen', 'June Lake Loop', None)])
        self.assertEqual((self.front/self.path).read_bytes(), self.image)
        self.assertEqual(self.apply()['status'], 'ALREADY_PRESENT')
        self.assertEqual(len(list((self.root/'backups').iterdir())), 1)

    def test_unpublished_local_edits_block_preparation(self):
        self.sql("UPDATE photography_catalog SET title='Local edit'", self.working)
        with self.assertRaisesRegex(ValueError, 'unpublished'):
            removal.prepare(self.base, self.working, self.path, self.front, self.root/'other.zip')

    def test_remote_edit_after_preflight_blocks(self):
        self.assertTrue(removal.status(self.live, self.payload, self.front).startswith('EXPECTED TEXT MATCHES'))
        self.sql("UPDATE photography_catalog SET title='Road edit'")
        with self.assertRaisesRegex(ValueError, 'CONFLICT'):
            self.apply()
        self.assertEqual(self.rows(self.live, 'photography_catalog')[0][2], 'Road edit')

    def test_rotation_does_not_block_removal(self):
        self.sql('UPDATE photography_catalog SET display_count=500,is_currently_displayed=0')
        self.assertEqual(self.apply()['status'], 'APPLIED')

    def test_changed_or_missing_image_blocks(self):
        target = self.front/self.path
        target.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'CONFLICT'):
            self.apply()
        target.unlink()
        with self.assertRaisesRegex(ValueError, 'CONFLICT'):
            self.apply()
        self.assertEqual(len(self.rows(self.live, 'photography_catalog')), 1)

    def test_delete_failure_rolls_back_detached_draft(self):
        self.sql("CREATE TRIGGER reject_removal BEFORE DELETE ON photography_catalog BEGIN SELECT RAISE(ABORT,'test'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            self.apply()
        self.assertEqual(self.rows(self.live, 'google_photo_drafts')[0][3], 17)
        self.assertEqual(len(self.rows(self.live, 'photography_catalog')), 1)

    def test_foreign_key_reference_prevents_removal(self):
        self.sql('CREATE TABLE photo_reference(photo_id INTEGER REFERENCES photography_catalog(image_id))')
        self.sql('INSERT INTO photo_reference VALUES(17)')
        with self.assertRaises(sqlite3.IntegrityError):
            self.apply()
        self.assertEqual(self.rows(self.live, 'google_photo_drafts')[0][3], 17)

    def test_invalid_payload_and_extra_files_rejected(self):
        payload = copy.deepcopy(self.payload)
        payload['file_path'] = '../other.webp'
        with self.assertRaises(ValueError):
            removal.validate(payload)
        with zipfile.ZipFile(self.package, 'a') as archive:
            archive.writestr('extra.txt', 'not allowed')
        with self.assertRaises(ValueError):
            preview(self.package.read_bytes())

    def test_helper_detects_later_local_changes(self):
        with patch.object(helper, 'ROOT', self.root), patch.object(helper, 'save'):
            helper.prepare_photo_removal(self.state, self.path)
            self.assertEqual(helper.current_job(self.state)['kind'], 'photo-remove')
            self.sql("UPDATE photography_catalog SET title='Later edit'", self.working)
            with self.assertRaises(ValueError):
                helper.current_job(self.state)

    def test_bring_home_detaches_preserved_local_draft_after_removal(self):
        self.apply()
        self.live.with_name('snapshot.json').write_text(json.dumps(dict(
            source='/home/cwoo/chi-portfolio/backend/portfolio.db',
            sha256=hashlib.sha256(self.live.read_bytes()).hexdigest())))
        with patch.object(photo_home, 'remote_manifest', return_value={}), patch.object(helper, 'save') as save:
            result = refresh(self.state, self.live, self.root/'copies', save, frontend=self.front)
        self.assertTrue(result['safe'])
        self.assertEqual(self.rows(self.state['working'], 'photography_catalog'), [])
        self.assertEqual(self.rows(self.state['working'], 'google_photo_drafts')[0][3], None)
        self.assertEqual(self.rows(self.working, 'google_photo_drafts')[0][3], 17)
        self.assertEqual((self.front/self.path).read_bytes(), self.image)

    def test_bring_home_does_not_discard_local_edits_to_removed_photo(self):
        self.apply()
        self.sql("UPDATE photography_catalog SET title='Unpublished'", self.working)
        with closing(sqlite3.connect(self.base)) as b, closing(sqlite3.connect(self.working)) as w, closing(sqlite3.connect(self.live)) as r:
            plan = photo_home.reconcile(b, w, r)
        self.assertIn(self.path, plan['blocked'])
