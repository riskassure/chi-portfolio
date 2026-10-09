import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import test_inspect_staged_package as fixtures
from prepare_math_patch import prepare
from apply_math_text_patch import patch_intended
from inspect_staged_package import preview


class PreparePatchTests(unittest.TestCase):
    def test_package_and_preview_synonym_changes(self):
        entry = fixtures.InspectTests().entry()
        canonical = entry.pop('canonical_name')
        updated = dict(entry, cleaned_tex='New text.', synonyms=['new alias'])
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / 'patch.zip'
            with patch('prepare_math_patch.read_snapshot', side_effect=[{canonical: entry}, {canonical: updated}]):
                report = prepare(Path('base'), Path('local'), canonical, output)
            self.assertIn('Synonyms added: ["new alias"]', report)
            with zipfile.ZipFile(output) as archive:
                payload = json.loads(archive.read('patch.json'))
            self.assertEqual(patch_intended(payload), updated)
            with patch('inspect_staged_package.read_snapshot', return_value={canonical: dict(entry, synonyms=['live alias'])}):
                self.assertIn('CONFLICT', preview(output.read_bytes(), Path('live')))
            with patch('inspect_staged_package.read_snapshot', return_value={canonical: updated}):
                self.assertIn('ALREADY PRESENT', preview(output.read_bytes(), Path('live')))
            with self.assertRaises(ValueError):
                patch_intended(dict(payload, replacement_synonyms=['same', 'SAME']))

    def test_unsupported_changes_refused(self):
        entry = fixtures.InspectTests().entry()
        canonical = entry.pop('canonical_name')
        with patch('prepare_math_patch.read_snapshot', side_effect=[{canonical: entry}, {canonical: dict(entry, title='Other')} ]):
            with self.assertRaises(ValueError):
                prepare(Path('base'), Path('local'), canonical, Path('unused.zip'))
