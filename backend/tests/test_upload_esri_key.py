import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import upload_esri_key as uploader


class UploadKeyTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / 'key.txt'

    def test_key_only_on_stdin_and_verified_result(self):
        self.path.write_text('\ufeffdummy-browser-key\n', encoding='utf-8')
        with patch.object(uploader.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, b'ESRI_KEY_INSTALLED\n', b'')) as run:
            result = uploader.upload('cwoo', self.path)
        self.assertNotIn('dummy-browser-key', result)
        self.assertEqual(run.call_args.kwargs['input'], b'dummy-browser-key')
        self.assertNotIn('dummy-browser-key', str(run.call_args.args))
        compile(uploader.REMOTE_SCRIPT, '<remote>', 'exec')

    def test_invalid_keys_and_accounts_never_connect(self):
        with patch.object(uploader.subprocess, 'run') as run:
            for value in ['', 'spaces in key', 'x' * 8193]:
                self.path.write_text(value)
                with self.assertRaises(ValueError):
                    uploader.upload('cwoo', self.path)
            with self.assertRaises(ValueError):
                uploader.upload('-bad-user', self.path)
            run.assert_not_called()

    def test_failure_output_is_not_disclosed(self):
        self.path.write_text('dummy-browser-key')
        for result in [subprocess.CompletedProcess([], 1, b'dummy-browser-key', b'secret server details'),
                       subprocess.CompletedProcess([], 0, b'Unexpected response', b'')]:
            with patch.object(uploader.subprocess, 'run', return_value=result):
                with self.assertRaises(ValueError) as error:
                    uploader.upload('cwoo', self.path)
                self.assertNotIn('dummy-browser-key', str(error.exception))
                self.assertNotIn('secret server', str(error.exception))


if __name__ == '__main__':
    unittest.main()
