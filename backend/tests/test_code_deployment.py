import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch
from urllib.error import URLError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import frontend_sync as files
import site_deployment as deploy
import website_workflow as helper
from inspect_staged_package import preview
from live_math_publication import publish


class CodeDeploymentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.server = self.root/'server'
        self.local = self.root/'local'
        self.paths = ['backend/src/routes/example.py', 'frontend/example.js']
        self.old = ['VALUE = 1\n', 'const value = 1;\n']
        self.new = ['VALUE = 2\n', 'const value = 2;\n']
        for root, values in ((self.server, self.old), (self.local, self.new)):
            for path, value in zip(self.paths, values):
                target = root/path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(value.encode())
        self.package = self.root/'package.zip'
        self.payload = files.prepare(self.local, self.paths, dict(zip(self.paths, self.old)), self.package, code=True)
        self.settings = dict(username='cwoo', token='fake-token')

    def test_paired_code_package_dispatch_and_backup(self):
        self.assertIn('Python syntax is checked without execution', preview(self.package.read_bytes()))
        database = self.server/'backend/portfolio.db'
        result = publish(self.package.read_bytes(), database, self.root/'backups', database.parent/'src')
        self.assertEqual(result['status'], 'APPLIED')
        self.assertFalse(database.exists())
        for path, value in zip(self.paths, self.new):
            self.assertEqual((self.server/path).read_text(), value)
        self.assertEqual((Path(result['backup'])/'0.before').read_text(), self.old[0])
        report = preview(self.package.read_bytes(), database, live=True)
        self.assertTrue(report.splitlines()[-3].startswith('ALREADY PRESENT'))

    def test_invalid_python_stops_before_mutation(self):
        payload = copy.deepcopy(self.payload)
        payload['files'][0]['replacement'] = 'def broken(:\n'
        with self.assertRaisesRegex(ValueError, 'syntax check'):
            files.apply(payload, self.server, self.root/'backups')
        self.assertEqual((self.server/self.paths[0]).read_text(), self.old[0])

    def test_validation_does_not_execute_python(self):
        payload = copy.deepcopy(self.payload)
        payload['files'][0]['replacement'] = "raise RuntimeError('must not execute during review')\n"
        files.validate(payload)

    def test_code_paths_cannot_escape_scope(self):
        for path in ('backend/portfolio.db', 'backend/setup_pythonanywhere.py', '../private.py',
                     'backend/src/.private/key.py', 'frontend/secret.json', '/backend/src/app.py'):
            payload = copy.deepcopy(self.payload)
            payload['files'][0]['path'] = path
            with self.assertRaises(ValueError):
                files.validate(payload)
        payload = dict(kind='frontend-files', files=self.payload['files'])
        with self.assertRaises(ValueError):
            files.validate(payload)

    def test_live_conflict_blocks_paired_update(self):
        (self.server/self.paths[0]).write_text('VALUE = 3\n')
        with self.assertRaisesRegex(ValueError, 'CONFLICT'):
            files.apply(self.payload, self.server, self.root/'backups')
        self.assertEqual((self.server/self.paths[1]).read_text(), self.old[1])

    def test_reload_uses_post_and_confines_token_to_api(self):
        response = Mock(status=200)
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        opener = Mock()
        opener.open.return_value = response
        with patch.object(deploy, 'domains', return_value=['www.example.com']), patch.object(deploy, 'build_opener', return_value=opener):
            deploy.reload_site(self.settings, 'www.example.com')
            request = opener.open.call_args.args[0]
            self.assertEqual(request.method, 'POST')
            self.assertEqual(request.full_url, 'https://www.pythonanywhere.com/api/v0/user/cwoo/webapps/www.example.com/reload/')
            self.assertEqual(request.get_header('Authorization'), 'Token fake-token')
            deploy.verify_site('www.example.com')
            request = opener.open.call_args.args[0]
            self.assertEqual(request.method, 'GET')
            self.assertIsNone(request.get_header('Authorization'))

    def test_reload_rejects_other_accounts_domain(self):
        with patch.object(deploy, 'domains', return_value=['www.example.com']), patch.object(deploy, 'build_opener') as opener:
            with self.assertRaises(ValueError):
                deploy.reload_site(self.settings, 'unrelated.example.com')
            opener.assert_not_called()

    def test_reload_network_error_does_not_expose_token(self):
        opener = Mock()
        opener.open.side_effect = URLError('fake-token')
        with patch.object(deploy, 'domains', return_value=['www.example.com']), patch.object(deploy, 'build_opener', return_value=opener):
            with self.assertRaisesRegex(RuntimeError, 'unconfirmed') as error:
                deploy.reload_site(self.settings, 'www.example.com')
            self.assertNotIn('fake-token', str(error.exception))

    def test_deployment_failure_and_retry_receipts_are_separate_from_upload(self):
        settings = self.root/'settings.json'
        settings.write_text(json.dumps(self.settings))
        job = dict(kind='website-code', domain='www.example.com', result='APPLIED', package=str(self.package), sha256='a'*64,
                   preflight_status='ALREADY PRESENT - code matches')
        state = dict(username='cwoo', job=job)
        with patch.object(helper, 'current_job', return_value=job), patch.object(helper, 'check_live'), \
             patch.object(helper, 'save'), patch.object(helper, 'SETTINGS', settings), \
             patch.object(deploy, 'reload_site') as reload, patch.object(deploy, 'verify_site') as verify:
            reload.side_effect = RuntimeError('unconfirmed')
            with self.assertRaises(RuntimeError):
                helper.finish_code_deployment(state)
            self.assertEqual(job['deployment_status'], 'RELOAD_PENDING')
            verify.assert_not_called()
            first = Path(job['deployment_receipt'])
            reload.side_effect = None
            helper.finish_code_deployment(state)
            self.assertEqual(job['deployment_status'], 'HOMEPAGE_VERIFIED')
            self.assertEqual(json.loads(first.read_text())['status'], 'RELOAD_PENDING')
            self.assertNotEqual(first, Path(job['deployment_receipt']))

    def test_reload_retry_refuses_changed_remote_files(self):
        job = dict(kind='website-code', result='APPLIED', preflight_status='CONFLICT - newer files')
        with patch.object(helper, 'current_job', return_value=job), patch.object(helper, 'check_live'), patch.object(deploy, 'reload_site') as reload:
            with self.assertRaisesRegex(ValueError, 'do not match'):
                helper.finish_code_deployment(dict(job=job))
            reload.assert_not_called()
