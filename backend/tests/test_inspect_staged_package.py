import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from inspect_staged_package import fetch_verified, preview


class InspectTests(unittest.TestCase):
    def entry(self):
        return dict(canonical_name='Test', slug='test', title='Test', owner='CWoo',
                    cleaned_tex='Original definition.', is_cleaned=1,
                    classifications=['54E35'], types=['Definition'], synonyms=[],
                    definitions=[], link_exclusions=[], related_concepts=[])

    def package(self, payload):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as archive:
            archive.writestr('entry.json', json.dumps(payload))
            archive.writestr('publisher.py', 'raise Exception("MUST NOT EXECUTE")')
        return buffer.getvalue()

    def test_preview_without_snapshot_does_not_claim_live_check(self):
        report = preview(self.package(self.entry()))
        self.assertIn('add one new entry', report)
        self.assertIn('Original definition.', report)
        self.assertIn('eligibility NOT CHECKED', report)

    def test_text_patch_reports_conflict_and_already_present(self):
        entry = self.entry()
        canonical = entry.pop('canonical_name')
        data = self.package(dict(canonical_name=canonical, expected=entry,
                                 replacement_tex='Revised definition.'))
        for current, status in [(entry, 'EXPECTED TEXT MATCHES'),
                                (dict(entry, cleaned_tex='Other edit.'), 'CONFLICT'),
                                (dict(entry, cleaned_tex='Revised definition.'), 'ALREADY PRESENT')]:
            with patch('inspect_staged_package.read_snapshot', return_value={canonical: current}):
                report = preview(data, Path('snapshot.db'))
            self.assertIn(status, report)
            self.assertIn('-Original definition.', report)
            self.assertIn('+Revised definition.', report)

    def test_fetch_only_get_and_mismatch_rejected(self):
        data = self.package(self.entry())
        with tempfile.TemporaryDirectory() as temp:
            local = Path(temp) / 'package.zip'
            local.write_bytes(data)
            opener = MagicMock()
            response = opener.open.return_value.__enter__.return_value
            response.read.return_value = data
            remote = '/home/cwoo/chi-portfolio-staging/' + 'a'*32 + '/package.zip'
            settings = dict(username='cwoo', token='test-token')
            with patch('inspect_staged_package.build_opener', return_value=opener):
                self.assertEqual(fetch_verified(settings, remote, local), data)
                self.assertEqual(opener.open.call_args.args[0].get_method(), 'GET')
                response.read.return_value = b'changed'
                with self.assertRaisesRegex(ValueError, 'differs'):
                    fetch_verified(settings, remote, local)
                with self.assertRaisesRegex(ValueError, 'exact private staging'):
                    fetch_verified(settings, '/home/cwoo/chi-portfolio/backend/portfolio.db', local)

    def test_ambiguous_package_rejected(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as archive:
            archive.writestr('one.json', '{}')
            archive.writestr('two.json', '{}')
        with self.assertRaisesRegex(ValueError, 'exactly one'):
            preview(buffer.getvalue())
