import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import hosting_secrets

STRONG = 'kR7#vQ2!mZp9@Lx4&Tn8'
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
        message = hosting_secrets.change_password(self.path, self.answers(STRONG, STRONG),
                                                  confirm=self.fail)
        self.assertIn('Reload', message)
        self.assertNotIn(STRONG, message)
        self.assertEqual(self.saved(), dict(ORIGINAL, ADMIN_PASSWORD=STRONG))
        self.assertFalse(self.path.with_name('hosting.json.new').exists())
        if os.name == 'posix':
            self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)

    def test_refused_passwords_change_nothing(self):
        for replies in [('short', 'short'), ('new-password-abcdefgh', 'different-password-xyz'),
                        (ORIGINAL['ADMIN_PASSWORD'], ORIGINAL['ADMIN_PASSWORD'])]:
            with self.assertRaises(SystemExit):
                hosting_secrets.change_password(self.path, self.answers(*replies), confirm=self.fail)
            self.assertEqual(self.saved(), ORIGINAL)

    def test_weak_password_needs_a_yes(self):
        weak = 'chi-password-2024-abcd'
        with patch('builtins.print'):
            with self.assertRaises(SystemExit):
                hosting_secrets.change_password(self.path, self.answers(weak, weak), confirm=lambda prompt: 'n')
            self.assertEqual(self.saved(), ORIGINAL)
            hosting_secrets.change_password(self.path, self.answers(weak, weak), confirm=lambda prompt: 'yes')
        self.assertEqual(self.saved()['ADMIN_PASSWORD'], weak)

    def test_weaknesses(self):
        self.assertEqual(hosting_secrets.weaknesses(STRONG), [])
        for weak, reason in [('xK9mP2vL8nQ4wR7tB3', 'shorter'), ('alllowercaselettersonlyhere', 'kinds'),
                             ('Admin-Zq8#vT2!kW9@xL', 'admin'), ('Zq8#vT2!kW9@xL1999ab', 'year'),
                             ('Zq8#vT2!kW9@xLaaa7Pm', 'repeats one'), ('Zq8#vT2!kW9@xL1234Pm', 'run'),
                             ('Ab1!Ab1!Ab1!Ab1!Ab1!', 'half')]:
            self.assertIn(reason, ' '.join(hosting_secrets.weaknesses(weak)), weak)

    def test_check_never_shows_the_password(self):
        message, strong = hosting_secrets.check_password(self.path)
        self.assertFalse(strong)
        self.assertNotIn(ORIGINAL['ADMIN_PASSWORD'], message)
        self.assertIn('hosting_secrets.py password', message)
        self.path.write_text(json.dumps(dict(ORIGINAL, ADMIN_PASSWORD=STRONG)), encoding='utf-8')
        self.assertEqual(hosting_secrets.check_password(self.path), ('No common weaknesses found.', True))

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
