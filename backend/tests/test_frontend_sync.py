import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import frontend_sync as files
import website_workflow as helper
from inspect_staged_package import preview
from live_math_publication import publish
from preflight_live_package import build_request


class FrontendSyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.front = self.root/'frontend'
        self.local = self.root/'local'
        self.front.mkdir()
        self.local.mkdir()
        (self.front/'page.html').write_bytes(b'<p>Before</p>\r\n')
        (self.local/'page.html').write_bytes(b'<p>After</p>\r\n')
        (self.local/'style.css').write_bytes(b'p { color: blue; }\n')
        self.paths = ['page.html', 'style.css']
        self.live = {path: files.read_text(self.front, path) for path in self.paths}
        self.package = self.root/'package.zip'
        self.payload = files.prepare(self.local, self.paths, self.live, self.package)
        self.backups = self.root/'backups'

    def apply(self):
        return files.apply(self.payload, self.front, self.backups)

    def test_review_and_publication_backups_preserve_exact_bytes(self):
        report = preview(self.package.read_bytes())
        self.assertIn('-<p>Before</p>', report)
        self.assertIn('+<p>After</p>', report)
        # File-only publication must work without opening/creating a database.
        database = self.root/'backend'/'portfolio.db'
        result = publish(self.package.read_bytes(), database, self.backups, database.parent/'src')
        self.assertFalse(database.exists())
        self.assertEqual(result['status'], 'APPLIED')
        backup = Path(result['backup'])
        self.assertEqual((backup/'0.before').read_bytes(), b'<p>Before</p>\r\n')
        self.assertEqual(json.loads((backup/'manifest.json').read_text())['status'], 'APPLIED')
        for path in self.paths:
            self.assertEqual((self.front/path).read_bytes(), (self.local/path).read_bytes())
        self.assertEqual(self.apply()['status'], 'ALREADY_PRESENT')
        self.assertEqual(len(list(self.backups.iterdir())), 1)

    def test_newer_live_file_blocks_entire_batch(self):
        (self.front/'page.html').write_text('Road edit', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'CONFLICT'):
            self.apply()
        self.assertFalse((self.front/'style.css').exists())
        self.assertEqual((self.front/'page.html').read_text(), 'Road edit')

    def test_changed_new_file_blocks_instead_of_overwriting(self):
        (self.front/'style.css').write_text('new live file', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'CONFLICT'):
            self.apply()
        self.assertEqual((self.front/'page.html').read_bytes(), b'<p>Before</p>\r\n')

    def test_failure_restores_previously_replaced_file(self):
        with patch.object(files.os, 'link', side_effect=OSError('transfer failed')):
            with self.assertRaises(OSError):
                self.apply()
        self.assertEqual((self.front/'page.html').read_bytes(), b'<p>Before</p>\r\n')
        self.assertFalse((self.front/'style.css').exists())
        self.assertFalse((self.backups/'.frontend-publish.lock').exists())
        manifest = next(self.backups.glob('*/manifest.json'))
        self.assertEqual(json.loads(manifest.read_text())['status'], 'ROLLED_BACK')

    def test_external_edit_is_not_destroyed_during_rollback(self):
        def fail_link(*args):
            (self.front/'page.html').write_text('Concurrent edit', encoding='utf-8')
            raise OSError('failed')
        with patch.object(files.os, 'link', side_effect=fail_link):
            with self.assertRaisesRegex(RuntimeError, 'manual recovery'):
                self.apply()
        self.assertEqual((self.front/'page.html').read_text(), 'Concurrent edit')
        self.assertTrue((self.backups/'.frontend-publish.lock').is_dir())
        with self.assertRaisesRegex(ValueError, 'locked'):
            self.apply()

    def test_preexisting_lock_prevents_publication(self):
        (self.backups/'.frontend-publish.lock').mkdir(parents=True)
        with self.assertRaisesRegex(ValueError, 'locked'):
            self.apply()
        self.assertEqual((self.front/'page.html').read_bytes(), b'<p>Before</p>\r\n')

    def test_backup_failure_does_not_touch_live_files(self):
        real_write = Path.write_bytes
        def fail_backup(path, content):
            if path.suffix == '.before':
                raise OSError('disk full')
            return real_write(path, content)
        with patch.object(Path, 'write_bytes', fail_backup):
            with self.assertRaises(OSError):
                self.apply()
        self.assertEqual((self.front/'page.html').read_bytes(), b'<p>Before</p>\r\n')

    def test_unsafe_private_backend_and_duplicate_paths_rejected(self):
        for path in ('../secret.js', '/page.html', 'a\\b.js', '.private/a.js', 'backend.py', 'settings.json', 'a/../b.css'):
            payload = copy.deepcopy(self.payload)
            payload['files'][0]['path'] = path
            with self.assertRaises(ValueError):
                files.validate(payload)
        payload = copy.deepcopy(self.payload)
        payload['files'].append(dict(payload['files'][0], path='PAGE.html'))
        with self.assertRaises(ValueError):
            files.validate(payload)

    def test_binary_deletions_and_oversize_files_rejected(self):
        for replacement in (None, '\x00binary', 'a'*(files.FILE_LIMIT+1)):
            payload = copy.deepcopy(self.payload)
            payload['files'][0]['replacement'] = replacement
            with self.assertRaises(ValueError):
                files.validate(payload)

    def test_unexpected_archive_member_rejected(self):
        with zipfile.ZipFile(self.package, 'a') as archive:
            archive.writestr('script.py', 'print(1)')
        with self.assertRaises(ValueError):
            preview(self.package.read_bytes())

    def test_no_difference_does_not_create_package(self):
        with self.assertRaisesRegex(ValueError, 'already match'):
            files.prepare(self.front, ['page.html'], {'page.html': self.live['page.html']}, self.root/'none.zip')
        self.assertFalse((self.root/'none.zip').exists())

    def test_missing_local_file_is_not_a_deletion(self):
        with self.assertRaisesRegex(ValueError, 'missing'):
            files.prepare(self.local, ['missing.js'], {'missing.js': 'live'}, self.root/'none.zip')

    def test_helper_detects_local_edit_after_review(self):
        baseline = self.root/'base.db'
        baseline.write_bytes(b'unchanged baseline')
        state = dict(base=str(baseline), base_sha256=hashlib.sha256(baseline.read_bytes()).hexdigest(), username='cwoo')
        with patch.object(helper, 'ROOT', self.root), patch.object(helper, 'save'), patch.object(files, 'capture_live', return_value={'page.html': 'older'}):
            helper.prepare_frontend(state, ['page.html'])
            self.assertEqual(helper.current_job(state)['kind'], 'frontend-files')
            (self.front/'page.html').write_text('another local edit', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'changed since review'):
                helper.current_job(state)

    def test_trusted_remote_module_list_loads_and_previews_files(self):
        request = build_request('cwoo', '/home/cwoo/chi-portfolio-staging/'+'a'*32+'/package.zip', self.package)
        self.assertIn('frontend_sync', [name for name, _ in request['modules']])
        # The remote copy has a synthetic __file__, not the local repository path.
        namespace = {'__file__': '<trusted>/frontend_sync.py'}
        source = dict(request['modules'])['frontend_sync']
        exec(compile(source, namespace['__file__'], 'exec'), namespace)
        self.assertIn('EXPECTED TEXT MATCHES', namespace['status'](self.payload, self.front))

    def test_live_reader_uses_validated_paths_and_handles_banner(self):
        result = Mock(stdout='SSH banner\nFRONTEND_SNAPSHOT='+json.dumps(self.live)+'\n')
        with patch.object(files.subprocess, 'run', return_value=result) as command:
            self.assertEqual(files.capture_live('cwoo', self.paths), self.live)
            request = json.loads(command.call_args.kwargs['input'])
            scope = {}
            exec(compile(request['reader'], '<reader>', 'exec'), scope)
            self.assertEqual(scope['read_text'](self.front, 'page.html'), self.live['page.html'])
            with self.assertRaises(ValueError):
                files.capture_live('bad;command', self.paths)

    def test_symbolic_link_is_rejected(self):
        with patch.object(Path, 'is_symlink', return_value=True):
            with self.assertRaises(ValueError):
                files.read_text(self.front, 'page.html')
