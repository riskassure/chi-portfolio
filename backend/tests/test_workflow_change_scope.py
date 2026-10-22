from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import website_workflow as helper
import prepare_math_patch


def entry(**changes):
    record = dict(slug='metric-space', title='metric space', owner='chi', cleaned_tex='A metric space is a set.',
                  is_cleaned=1, classifications=['54E35'], types=['Definition'], synonyms=['distance space'],
                  definitions=[], link_exclusions=[], related_concepts=[])
    record.update(changes)
    return record


class ChangeScopeTests(unittest.TestCase):
    """Option 1 must report the same scope that option 2 enforces, with a reason."""

    def scan(self, baseline, working):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)/'base.db'
            base.write_bytes(b'baseline')
            state = dict(base=str(base), base_sha256=helper.digest(base), working='working.db')
            snapshots = {str(base): baseline, 'working.db': working}
            with patch.object(helper, 'read_snapshot', side_effect=lambda path: snapshots[str(path)]):
                return {item['canonical']: item for item in helper.changed_entries(state)}

    def test_plain_text_and_new_entries_stay_supported(self):
        changes = self.scan({'MetricSpace': entry()},
                            {'MetricSpace': entry(cleaned_tex='A metric space is a set with a distance.'),
                             'NormedSpace': entry(slug='normed-space', title='normed space')})
        self.assertTrue(changes['MetricSpace']['supported'])
        self.assertIsNone(changes['MetricSpace']['reason'])
        self.assertTrue(changes['NormedSpace']['supported'])

    def test_existing_diagram_entry_is_flagged_before_option_2(self):
        tex = 'See the figure.\n\\begin{pspicture}(0,0)(1,1)\\end{pspicture}'
        changes = self.scan({'VennDiagram': entry(cleaned_tex=tex)},
                            {'VennDiagram': entry(cleaned_tex=tex + '\nMore text.')})
        item = changes['VennDiagram']
        self.assertFalse(item['supported'])
        self.assertIn('baseline (live) entry contains diagrams or images', item['reason'])

    def test_missing_classification_and_duplicate_metadata_are_named(self):
        changes = self.scan({'Percentile': entry(classifications=[]),
                             'Hypergroup': entry(definitions=['absolute identity', 'absolute identity'])},
                            {'Percentile': entry(classifications=[], cleaned_tex='Edited.'),
                             'Hypergroup': entry(definitions=['absolute identity', 'absolute identity'],
                                                 cleaned_tex='Edited.')})
        self.assertIn('has no MSC classification', changes['Percentile']['reason'])
        self.assertIn("definitions has duplicate or untrimmed values: 'absolute identity'",
                      changes['Hypergroup']['reason'])

    def test_local_edit_that_adds_media_or_bad_synonyms_is_flagged(self):
        changes = self.scan({'A': entry(), 'B': entry()},
                            {'A': entry(cleaned_tex='Text \\includegraphics{x.png}'),
                             'B': entry(synonyms=['Distance space', 'distance space'])})
        self.assertTrue(changes['A']['reason'].startswith('local version contains diagrams or images'))
        self.assertIn('differs only in capitalization', changes['B']['reason'])

    def test_other_field_changes_deletions_and_bad_new_entries(self):
        changes = self.scan({'A': entry(), 'Gone': entry()},
                            {'A': entry(types=['Theorem']),
                             "Euler'stheorem": entry(slug="euler'stheorem")})
        self.assertIn('changes types; only content and synonym changes', changes['A']['reason'])
        self.assertIn('deletions are not supported', changes['Gone']['reason'])
        self.assertIn('new entry slug', changes["Euler'stheorem"]['reason'])

    def test_option_2_refuses_with_the_same_reason(self):
        candidate = dict(canonical='Deduction', supported=False, new=False,
                         reason='baseline (live) entry contains diagrams or images')
        with patch.object(helper, 'changed_entries', return_value=[candidate]):
            with self.assertRaisesRegex(ValueError, 'baseline \\(live\\) entry contains diagrams'):
                helper.prepare_selected({}, 'Deduction')

    def test_option_1_agrees_with_the_option_2_preparers(self):
        pstricks = '\\begin{pspicture}(0,0)(1,1)\\end{pspicture}'
        baseline = {'Text': entry(), 'Diagram': entry(cleaned_tex=pstricks), 'Unclassified': entry(classifications=[]),
                    'Untyped': entry(types=[]), 'Duplicate': entry(synonyms=['ring', 'ring']),
                    'Synonyms': entry(), 'CaseSynonyms': entry(), 'AddsImage': entry()}
        working = {'Text': entry(cleaned_tex='Edited.'), 'Diagram': entry(cleaned_tex=pstricks + ' Edited.'),
                   'Unclassified': entry(classifications=[], cleaned_tex='Edited.'),
                   'Untyped': entry(types=[], cleaned_tex='Edited.'),
                   'Duplicate': entry(synonyms=['ring', 'ring'], cleaned_tex='Edited.'),
                   'Synonyms': entry(synonyms=['distance space', 'metric']),
                   'CaseSynonyms': entry(synonyms=['Metric', 'metric']),
                   'AddsImage': entry(cleaned_tex='<img src="x.png">'),
                   'NewText': entry(slug='new-text', title='new text'),
                   'NewDiagram': entry(slug='new-diagram', title='new diagram', cleaned_tex=pstricks),
                   'NewBadSlug': entry(slug='New_Slug', title='new slug')}
        changes = self.scan(baseline, working)
        self.assertEqual(set(changes), set(working))
        with tempfile.TemporaryDirectory() as temp, \
             patch.object(prepare_math_patch, 'read_snapshot', side_effect=lambda path: baseline if path == 'b' else working):
            for name, item in changes.items():
                with self.subTest(name):
                    try:
                        if item['new']:
                            helper.validate_entry(dict(working[name], canonical_name=name))
                        else:
                            prepare_math_patch.prepare('b', 'w', name, Path(temp)/(name + '.zip'))
                        accepted = True
                    except ValueError:
                        accepted = False
                    self.assertEqual(item['supported'], accepted, item['reason'])
        self.assertEqual({name for name, item in changes.items() if item['supported']}, {'Text', 'Synonyms', 'NewText'})


if __name__ == '__main__':
    unittest.main()
