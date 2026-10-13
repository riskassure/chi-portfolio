from contextlib import closing
import hashlib
from io import BytesIO
import json
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PIL import Image
from bring_changes_home import refresh
import photo_home


class PhotoHomeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.front = self.root/'frontend'
        self.front.mkdir()
        self.base, self.local, self.live = [self.root/name for name in ('base.db', 'local.db', 'live.db')]
        with closing(sqlite3.connect(self.base)) as db:
            db.executescript('''
                CREATE TABLE math_concepts(id INTEGER PRIMARY KEY, content TEXT);
                CREATE TABLE photography_catalog(image_id INTEGER PRIMARY KEY, file_path TEXT UNIQUE,
                    title TEXT, location_name TEXT, latitude REAL, longitude REAL,
                    is_currently_displayed INTEGER, last_displayed_date TEXT, display_count INTEGER);
            ''')
        for target in (self.local, self.live):
            shutil.copyfile(self.base, target)
        self.state = dict(base=str(self.base), working=str(self.local), username='cwoo',
                          base_sha256=self.hash(self.base), job={'review': 'keep'})
        self.save = Mock()
        self.path = 'images/photography/aspen.webp'
        buffer = BytesIO()
        Image.new('RGB', (10, 10), 'green').save(buffer, 'WEBP')
        self.image = buffer.getvalue()
        self.manifest = {self.path: dict(sha256=hashlib.sha256(self.image).hexdigest(), size=len(self.image))}
        self.remote = patch.object(photo_home, 'remote_manifest', return_value=self.manifest).start()
        self.addCleanup(patch.stopall)
        self.scp = patch.object(photo_home.subprocess, 'run', side_effect=self.transfer).start()

    def hash(self, path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def transfer(self, command, **kwargs):
        self.assertEqual(command[0], 'scp')
        Path(command[-1]).write_bytes(self.image)

    def sql(self, path, sql, args=()):
        with closing(sqlite3.connect(path)) as db:
            db.execute(sql, args)
            db.commit()

    def add_photo(self, database, image_id=1, title='Aspen'):
        self.sql(database, 'INSERT INTO photography_catalog VALUES(?,?,?,?,?,?,?,NULL,0)',
                 (image_id, self.path, title, 'June Lake Loop', 0, 0, 1))

    def add_draft(self, linked=1):
        self.sql(self.local, photo_home.DRAFT_SQL)
        self.sql(self.local, 'INSERT INTO google_photo_drafts VALUES(?,?,?,?)',
                 ('a'*64, 'Aspen', 'June Lake Loop', linked))

    def run_refresh(self):
        self.live.with_name('snapshot.json').write_text(json.dumps(dict(
            source='/home/cwoo/chi-portfolio/backend/portfolio.db', sha256=self.hash(self.live))))
        return refresh(self.state, self.live, self.root/'copies', self.save, frontend=self.front)

    def test_live_photo_downloaded_before_switch_and_old_databases_preserved(self):
        self.add_photo(self.live)
        before = self.hash(self.local)
        result = self.run_refresh()
        self.assertTrue(result['safe'])
        self.assertEqual(result['photos_downloaded'], 1)
        self.assertEqual((self.front/self.path).read_bytes(), self.image)
        self.assertEqual(self.hash(self.local), before)
        self.assertEqual(self.hash(Path(self.state['base'])), self.hash(self.live))
        self.save.assert_called_once()

    def test_published_local_photo_draft_remapped_and_pending_draft_preserved(self):
        self.add_photo(self.local, 3)
        self.add_photo(self.live, 17)
        self.add_draft(3)
        self.sql(self.local, 'INSERT INTO google_photo_drafts VALUES(?,?,?,NULL)', ('b'*64, 'Pending', 'Elsewhere'))
        self.sql(self.live, 'UPDATE photography_catalog SET display_count=10,last_displayed_date=?', ('today',))
        result = self.run_refresh()
        self.assertTrue(result['safe'])
        self.assertEqual(result['local_drafts_preserved'], 2)
        with closing(sqlite3.connect(self.state['working'])) as db:
            self.assertEqual(db.execute('SELECT published_id FROM google_photo_drafts ORDER BY digest').fetchall(), [(17,), (None,)])
        with closing(sqlite3.connect(self.state['base'])) as db:
            self.assertIsNone(db.execute("SELECT 1 FROM sqlite_master WHERE name='google_photo_drafts'").fetchone())
        # A second refresh must not treat preserved private drafts as conflicts.
        self.assertTrue(self.run_refresh()['safe'])

    def test_unpublished_local_photo_blocks_without_network(self):
        self.add_photo(self.local)
        self.assertFalse(self.run_refresh()['safe'])
        self.remote.assert_not_called()
        self.save.assert_not_called()

    def test_divergent_metadata_blocks(self):
        self.add_photo(self.local, title='Local title')
        self.add_photo(self.live, title='Remote title')
        self.assertFalse(self.run_refresh()['safe'])
        self.save.assert_not_called()

    def test_live_metadata_edit_and_unrelated_live_addition_allowed(self):
        for database in (self.base, self.local, self.live):
            self.add_photo(database)
        self.state['base_sha256'] = self.hash(self.base)
        self.sql(self.live, 'UPDATE photography_catalog SET location_name=?', ('Road edit',))
        self.assertTrue(self.run_refresh()['safe'])

    def test_existing_identical_file_not_downloaded(self):
        self.add_photo(self.live)
        target = self.front/self.path
        target.parent.mkdir(parents=True)
        target.write_bytes(self.image)
        self.assertEqual(self.run_refresh()['photos_downloaded'], 0)
        self.scp.assert_not_called()

    def test_different_local_file_preserved_and_switch_blocked(self):
        self.add_photo(self.live)
        target = self.front/self.path
        target.parent.mkdir(parents=True)
        target.write_bytes(b'local modification')
        original = dict(self.state)
        with self.assertRaises(ValueError):
            self.run_refresh()
        self.assertEqual(target.read_bytes(), b'local modification')
        self.assertEqual(self.state, original)
        self.save.assert_not_called()

    def test_corrupt_download_leaves_active_database_and_gallery_unchanged(self):
        self.add_photo(self.live)
        self.image = b'corrupt transport'
        with self.assertRaises(ValueError):
            self.run_refresh()
        self.assertFalse((self.front/self.path).exists())
        self.save.assert_not_called()

    def test_missing_remote_image_stops_switch(self):
        self.add_photo(self.live)
        self.remote.side_effect = RuntimeError('Missing remote file')
        with self.assertRaises(RuntimeError):
            self.run_refresh()
        self.save.assert_not_called()

    def test_traversal_is_rejected_before_network(self):
        self.add_photo(self.live)
        self.sql(self.live, 'UPDATE photography_catalog SET file_path=?', ('images/photography/../../secret.webp',))
        with self.assertRaises(ValueError):
            self.run_refresh()
        self.remote.assert_not_called()

    def test_remote_only_private_draft_blocks(self):
        self.sql(self.live, photo_home.DRAFT_SQL)
        self.sql(self.live, 'INSERT INTO google_photo_drafts VALUES(?,?,?,NULL)', ('a'*64, 'Remote draft', ''))
        self.assertFalse(self.run_refresh()['safe'])
        self.remote.assert_not_called()

    def test_save_failure_keeps_original_state_and_databases(self):
        self.add_photo(self.live)
        original = dict(self.state)
        before = self.hash(self.local)
        self.save.side_effect = OSError('disk full')
        with self.assertRaises(OSError):
            self.run_refresh()
        self.assertEqual(self.state, original)
        self.assertEqual(self.hash(self.local), before)
        # A verified extra image is harmless and reusable on retry.
        self.assertEqual((self.front/self.path).read_bytes(), self.image)

    def test_invalid_manifest_rejected(self):
        self.add_photo(self.live)
        self.manifest[self.path]['size'] = -1
        with self.assertRaises(ValueError):
            self.run_refresh()
        self.save.assert_not_called()

    def test_concurrent_image_creation_never_overwritten(self):
        self.add_photo(self.live)
        def raced_link(source, destination):
            Path(destination).write_bytes(b'concurrent image')
            raise FileExistsError()
        with patch.object(photo_home.os, 'link', side_effect=raced_link):
            with self.assertRaises(ValueError):
                self.run_refresh()
        self.assertEqual((self.front/self.path).read_bytes(), b'concurrent image')
        self.save.assert_not_called()

    def test_other_media_changes_still_block(self):
        for database in (self.base, self.local, self.live):
            self.sql(database, 'CREATE TABLE music_catalog(id INTEGER, path TEXT)')
        self.state['base_sha256'] = self.hash(self.base)
        self.sql(self.live, "INSERT INTO music_catalog VALUES(1,'song.mp3')")
        self.assertFalse(self.run_refresh()['safe'])
        self.remote.assert_not_called()

    def test_unrecognized_photo_column_does_not_silently_lose_edits(self):
        for database in (self.base, self.local, self.live):
            self.sql(database, 'ALTER TABLE photography_catalog ADD COLUMN caption TEXT')
        self.state['base_sha256'] = self.hash(self.base)
        with self.assertRaisesRegex(ValueError, 'Unrecognized gallery schema'):
            self.run_refresh()
        self.remote.assert_not_called()

    def test_later_download_failure_does_not_install_earlier_images(self):
        self.add_photo(self.live)
        second = 'images/photography/second.webp'
        self.sql(self.live, 'INSERT INTO photography_catalog VALUES(2,?,?,?,?,1,1,NULL,0)',
                 (second, 'Second', 'Place', 0))
        self.manifest[second] = dict(self.manifest[self.path])
        count = 0
        def transfer(command, **kwargs):
            nonlocal count
            count += 1
            Path(command[-1]).write_bytes(self.image if count == 1 else b'bad')
        self.scp.side_effect = transfer
        with self.assertRaises(ValueError):
            self.run_refresh()
        self.assertFalse((self.front/self.path).exists())
        self.save.assert_not_called()

    def test_failed_refresh_report_is_not_marked_complete(self):
        self.add_photo(self.live)
        self.save.side_effect = OSError('disk full')
        with self.assertRaises(OSError):
            self.run_refresh()
        report = next((self.root/'copies').glob('*/comparison.json'))
        self.assertFalse(json.loads(report.read_text())['refresh_complete'])


class ManifestTests(unittest.TestCase):
    def test_remote_script_compiles_and_manifest_ignores_login_banner(self):
        compile(photo_home.MANIFEST_SCRIPT, '<manifest>', 'exec')
        path = 'images/photography/photo.webp'
        manifest = {path: {'sha256': 'a'*64, 'size': 20}}
        with patch.object(photo_home.subprocess, 'run', return_value=Mock(
                stdout='SSH banner\nPHOTO_MANIFEST='+json.dumps(manifest)+'\n')) as command:
            self.assertEqual(photo_home.remote_manifest('cwoo', [path]), manifest)
            self.assertEqual(json.loads(command.call_args.kwargs['input'])['paths'], [path])

    def test_invalid_username_or_path_does_not_launch_ssh(self):
        with patch.object(photo_home.subprocess, 'run') as command:
            for username, path in [('bad;command', 'images/photography/a.webp'),
                                   ('cwoo', '../../secret')]:
                with self.assertRaises(ValueError):
                    photo_home.remote_manifest(username, [path])
            command.assert_not_called()
