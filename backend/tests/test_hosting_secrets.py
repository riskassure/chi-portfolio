import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import hosting_secrets

ORIGINAL = {'PUBLIC_ORIGIN': 'https://www.example', 'FLASK_SECRET_KEY': 's' * 64,
            'ADMIN_PASSWORD': 'old-password-123456'}


class HostingSecretsTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path = Path(folder.name) / 'hosting.json'
        self.path.write_text(json.dumps(ORIGINAL), encoding='utf-8')

    def answers(self, *replies):
        replies = iter(replies)
        return lambda prompt: next(replies)

    def saved(self):
        return json.loads(self.path.read_text(encoding='utf-8'))

    def test_password_change_keeps_other_settings(self):
        message = hosting_secrets.change_password(self.path, self.answers('new-password-abcdefgh', 'new-password-abcdefgh'))
        self.assertIn('Reload', message)
        self.assertNotIn('new-password', message)
        self.assertEqual(self.saved(), dict(ORIGINAL, ADMIN_PASSWORD='new-password-abcdefgh'))
        self.assertFalse(self.path.with_name('hosting.json.new').exists())
        if os.name == 'posix':
            self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)

    def test_refused_passwords_change_nothing(self):
        for replies in [('short', 'short'), ('new-password-abcdefgh', 'different-password-xyz'),
                        (ORIGINAL['ADMIN_PASSWORD'], ORIGINAL['ADMIN_PASSWORD'])]:
            with self.assertRaises(SystemExit):
                hosting_secrets.change_password(self.path, self.answers(*replies))
            self.assertEqual(self.saved(), ORIGINAL)

    def test_session_secret_change(self):
        hosting_secrets.change_session_secret(self.path)
        values = self.saved()
        self.assertNotEqual(values['FLASK_SECRET_KEY'], ORIGINAL['FLASK_SECRET_KEY'])
        self.assertGreaterEqual(len(values['FLASK_SECRET_KEY']), hosting_secrets.MIN_SECRET)
        self.assertEqual({k: v for k, v in values.items() if k != 'FLASK_SECRET_KEY'},
                         {k: v for k, v in ORIGINAL.items() if k != 'FLASK_SECRET_KEY'})

    def test_missing_settings_file_refused(self):
        self.path.unlink()
        with self.assertRaises(SystemExit):
            hosting_secrets.change_session_secret(self.path)
        self.assertFalse(self.path.exists())


if __name__ == '__main__':
    unittest.main()
