"""Exercise save failures and competing editor locks using disposable files."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from services.file_persistence import exclusive_edit, replace_text


class PersistenceTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.target = Path(temp.name) / 'settings.js'
        self.target.write_text('original')

    def test_competing_editor_cannot_remove_owners_lock(self):
        with exclusive_edit(self.target, ValueError, 'busy'):
            with self.assertRaisesRegex(ValueError, 'busy'):
                with exclusive_edit(self.target, ValueError, 'busy'):
                    self.fail('Second editor acquired lock')
            self.assertTrue(self.target.with_suffix('.lock').exists())
        self.assertFalse(self.target.with_suffix('.lock').exists())

    def test_flush_and_replace_failures_preserve_original_and_allow_retry(self):
        for operation in ('fsync', 'replace'):
            with self.subTest(operation=operation):
                with self.assertRaises(OSError), exclusive_edit(self.target, ValueError, 'busy'):
                    with patch('services.file_persistence.os.' + operation, side_effect=OSError('disk failure')):
                        replace_text(self.target, 'new', prefix='.test-')
                self.assertEqual(self.target.read_text(), 'original')
                self.assertEqual(list(self.target.parent.iterdir()), [self.target])
        with exclusive_edit(self.target, ValueError, 'busy'):
            replace_text(self.target, 'new\n', prefix='.test-')
        self.assertEqual(self.target.read_bytes(), b'new\n')

    def test_revision_recheck_preserves_external_edit(self):
        def changed():
            self.target.write_text('external edit')
            raise ValueError('stale')
        with self.assertRaisesRegex(ValueError, 'stale'), exclusive_edit(self.target, ValueError, 'busy'):
            replace_text(self.target, 'our edit', prefix='.test-', before_replace=changed)
        self.assertEqual(self.target.read_text(), 'external edit')
        self.assertEqual(list(self.target.parent.iterdir()), [self.target])


if __name__ == '__main__':
    unittest.main()
