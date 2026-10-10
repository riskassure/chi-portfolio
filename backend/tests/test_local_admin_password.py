import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import local_admin_password as passwords


@unittest.skipUnless(os.name == 'nt', 'Windows DPAPI')
class LocalPasswordTests(unittest.TestCase):
    def test_save_load_reset_and_session_override(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'password.dpapi'
            first = 'first-test-password-123'
            second = 'second-test-password-456'
            with patch.object(passwords.getpass, 'getpass', side_effect=[first, first]):
                self.assertEqual(passwords.get_password(path=path), first)
            self.assertNotIn(first.encode(), path.read_bytes())
            with patch.object(passwords.getpass, 'getpass', side_effect=AssertionError('Should not prompt')):
                self.assertEqual(passwords.get_password(path=path), first)
            old = path.read_bytes()
            with patch.object(passwords.getpass, 'getpass', side_effect=[second, 'mismatch']):
                with self.assertRaises(ValueError):
                    passwords.get_password(path=path, reset=True)
            self.assertEqual(path.read_bytes(), old)
            with patch.object(passwords.getpass, 'getpass', side_effect=[second, second]):
                self.assertEqual(passwords.get_password(path=path, session=True), second)
            self.assertEqual(path.read_bytes(), old)
            with patch.object(passwords.getpass, 'getpass', side_effect=[second, second]):
                passwords.get_password(path=path, reset=True)
            self.assertEqual(passwords.get_password(path=path), second)

    def test_corrupt_file_does_not_silently_replace_password(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'password.dpapi'
            path.write_bytes(b'invalid ciphertext')
            with patch.object(passwords.getpass, 'getpass', side_effect=AssertionError('Should not prompt')):
                with self.assertRaises(ValueError):
                    passwords.get_password(path=path)
            self.assertEqual(path.read_bytes(), b'invalid ciphertext')
