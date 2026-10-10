from contextlib import closing
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import tempfile
import unittest
from unittest.mock import Mock
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bring_changes_home import refresh


class BringHomeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.base = self.root/'base.db'
        self.local = self.root/'working.db'
        self.live = self.root/'live-snapshot.db'
        with closing(sqlite3.connect(self.base)) as db:
            db.executescript('''
                CREATE TABLE math_concepts(id INTEGER PRIMARY KEY, content TEXT);
                CREATE TABLE profile_page_revisions(id INTEGER PRIMARY KEY, content TEXT);
                CREATE TABLE photography_catalog(id INTEGER PRIMARY KEY, path TEXT);
                INSERT INTO math_concepts VALUES(1,'original');
                INSERT INTO profile_page_revisions VALUES(1,'original bio');
            ''')
        for target in (self.local, self.live):
            shutil.copyfile(self.base, target)
        self.state = dict(base=str(self.base), working=str(self.local),
                          base_sha256=self.hash(self.base), username='cwoo', job={'review': 'preserve me'})
        self.save = Mock()

    def hash(self, path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def edit(self, path, sql):
        with closing(sqlite3.connect(path)) as db:
            db.execute(sql)
            db.commit()

    def run_refresh(self):
        self.live.with_name('snapshot.json').write_text(json.dumps(dict(
            sha256=self.hash(self.live), source='/home/cwoo/chi-portfolio/backend/portfolio.db')))
        return refresh(self.state, self.live, self.root/'copies', self.save)

    def test_live_changes_create_new_copies_preserve_old(self):
        before = self.hash(self.local)
        self.edit(self.live, "UPDATE profile_page_revisions SET content='road edit'")
        result = self.run_refresh()
        self.assertTrue(result['safe'])
        self.assertEqual(self.hash(self.local), before)
        self.assertEqual(self.hash(Path(self.state['working'])), self.hash(self.live))
        self.assertEqual(self.hash(Path(self.state['base'])), self.hash(self.live))
        self.assertIsNone(self.state['job'])
        self.assertEqual(json.loads((Path(self.state['base']).parent/'previous-workflow.json').read_text())['job'], {'review': 'preserve me'})
        self.save.assert_called_once()

    def test_local_edit_blocks_even_outside_math(self):
        original = dict(self.state)
        self.edit(self.local, "UPDATE profile_page_revisions SET content='unpublished'")
        result = self.run_refresh()
        self.assertFalse(result['safe'])
        self.assertIn('profile_page_revisions', result['blocked'])
        self.assertEqual(self.state, original)
        self.save.assert_not_called()

    def test_identical_published_rows_allowed(self):
        for path in (self.local, self.live):
            self.edit(path, "UPDATE math_concepts SET content='published'")
        self.assertTrue(self.run_refresh()['safe'])

    def test_profile_save_times_ignored_but_history_checked(self):
        for path in (self.base, self.local, self.live):
            with closing(sqlite3.connect(path)) as db:
                db.execute('DROP TABLE profile_page_revisions')
                db.execute('CREATE TABLE profile_page_revisions(page TEXT,revision INTEGER,content TEXT,saved_at TEXT)')
                db.execute('INSERT INTO profile_page_revisions VALUES(?,?,?,?)', ('bio',1,'{"name":"Chi"}','original'))
                db.commit()
        self.state['base_sha256'] = self.hash(self.base)
        for path, timestamp, content in ((self.local,'local time','{"name":"Chi Woo"}'),
                                          (self.live,'live time','{ "name": "Chi Woo" }')):
            with closing(sqlite3.connect(path)) as db:
                db.execute('INSERT INTO profile_page_revisions VALUES(?,?,?,?)', ('bio',2,content,timestamp))
                db.commit()
        original_state = dict(self.state)
        self.assertTrue(self.run_refresh()['safe'])
        self.state = original_state
        self.save.reset_mock()
        self.edit(self.local, "UPDATE profile_page_revisions SET content='{\"name\":\"Unpublished\"}' WHERE revision=1")
        self.assertFalse(self.run_refresh()['safe'])
        self.save.assert_not_called()

    def test_changed_media_needs_review(self):
        self.edit(self.live, "INSERT INTO photography_catalog VALUES(1,'new-photo.jpg')")
        result = self.run_refresh()
        self.assertFalse(result['safe'])
        self.assertEqual(result['media_review'], ['photography_catalog'])
        self.save.assert_not_called()

    def test_schema_change_blocks(self):
        self.edit(self.live, 'ALTER TABLE math_concepts ADD COLUMN extra TEXT')
        self.assertFalse(self.run_refresh()['safe'])
        self.save.assert_not_called()

    def test_failed_save_preserves_original_state_and_databases(self):
        original = dict(self.state)
        before = self.hash(self.local)
        self.save.side_effect = OSError('disk full')
        with self.assertRaises(OSError):
            self.run_refresh()
        self.assertEqual(self.state, original)
        self.assertEqual(self.hash(self.local), before)

    def test_changed_baseline_rejected(self):
        self.edit(self.base, "UPDATE math_concepts SET content='changed baseline'")
        with self.assertRaisesRegex(ValueError, 'Baseline changed'):
            self.run_refresh()
        self.save.assert_not_called()

    def test_corrupt_snapshot_checksum_rejected(self):
        self.live.with_name('snapshot.json').write_text(json.dumps(dict(
            sha256='0'*64, source='/home/cwoo/chi-portfolio/backend/portfolio.db')))
        with self.assertRaises(ValueError):
            refresh(self.state, self.live, self.root/'copies', self.save)
        self.save.assert_not_called()
