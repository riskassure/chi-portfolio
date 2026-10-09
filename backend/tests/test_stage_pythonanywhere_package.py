import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from stage_pythonanywhere_package import read_package, stage


class StageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.package = Path(self.temp.name) / 'update.zip'
        self.settings = {'username': 'cwoo', 'token': 'private-token'}

    def make_zip(self, name='REVIEW.txt'):
        with zipfile.ZipFile(self.package, 'w') as archive:
            member = zipfile.ZipInfo('placeholder')
            member.filename = name  # Preserve hostile separators on Windows too.
            archive.writestr(member, 'reviewed content')
        return self.package.read_bytes()

    def response(self, data=b'', status=200):
        result = MagicMock()
        result.__enter__.return_value = result
        result.status = status
        result.read.return_value = data
        return result

    def test_upload_and_verification(self):
        data = self.make_zip()
        opener = MagicMock()
        opener.open.side_effect = [HTTPError('url',404,'missing',{},None),
                                   self.response(status=201), self.response(data)]
        with patch('stage_pythonanywhere_package.build_opener', return_value=opener):
            remote, digest = stage(self.settings, self.package)
        calls = [c.args[0] for c in opener.open.call_args_list]
        self.assertEqual([r.get_method() for r in calls], ['GET','POST','GET'])
        self.assertTrue(remote.startswith('/home/cwoo/chi-portfolio-staging/'))
        self.assertTrue(all(r.full_url.endswith(remote) for r in calls))
        self.assertIn(b'name="content"', calls[1].data)
        self.assertIn(data, calls[1].data)
        self.assertEqual(len(digest), 64)

    def test_collision_never_posts(self):
        self.make_zip()
        opener = MagicMock()
        opener.open.return_value = self.response()
        with patch('stage_pythonanywhere_package.build_opener', return_value=opener):
            with self.assertRaises(ValueError):
                stage(self.settings, self.package)
        self.assertEqual(opener.open.call_count, 1)

    def test_failed_verification_is_not_success(self):
        self.make_zip()
        opener = MagicMock()
        opener.open.side_effect = [HTTPError('url',404,'missing',{},None),
                                   self.response(status=201), self.response(b'wrong')]
        with patch('stage_pythonanywhere_package.build_opener', return_value=opener):
            with self.assertRaisesRegex(RuntimeError, 'unverified upload'):
                stage(self.settings, self.package)

    def test_invalid_packages_rejected(self):
        for name in ('../escape.py', '/absolute.py', 'folder\\escape.py',
                     '.env', 'portfolio.db', 'hosting.json', 'pythonanywhere-api.json'):
            with self.subTest(name=name):
                self.make_zip(name)
                with self.assertRaises(ValueError):
                    read_package(self.package)

    def test_auth_failure_redacted_no_post(self):
        self.make_zip()
        opener = MagicMock()
        opener.open.side_effect = HTTPError('url',403,'private-token',{},None)
        with patch('stage_pythonanywhere_package.build_opener', return_value=opener):
            with self.assertRaises(RuntimeError) as caught:
                stage(self.settings, self.package)
        self.assertNotIn('private-token', str(caught.exception))
        self.assertEqual(opener.open.call_count, 1)
