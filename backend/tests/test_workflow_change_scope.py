from contextlib import closing
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import website_workflow as helper
import prepare_math_patch
from services.math.render_helper import extract_all_pstricks_diagram_blocks

PICTURE = '\\begin{pspicture}(0,0)(1,1)\\end{pspicture}'


def entry(**changes):
    record = dict(slug='metric-space', title='metric space', owner='chi', cleaned_tex='A metric space is a set.',
                  is_cleaned=1, classifications=['54E35'], types=['Definition'], synonyms=['distance space'],
                  definitions=[], link_exclusions=[], related_concepts=[])
    record.update(changes)
    return record


class ChangeScopeTests(unittest.TestCase):
    """Option 1 must report the same scope that option 2 enforces, with a reason."""

    def working_db(self, folder, svgs):
        """A working database holding only stored diagram SVGs: {canonical: tex whose diagrams have SVGs}."""
        path = Path(folder)/'working.db'
        with closing(sqlite3.connect(path)) as db:
            db.execute('CREATE TABLE math_concepts(id INTEGER PRIMARY KEY, canonical_name TEXT)')
            db.execute('CREATE TABLE math_concept_diagrams(concept_id INTEGER, source_hash TEXT, svg_path TEXT)')
            for ident, (name, tex) in enumerate(svgs.items(), 1):
                db.execute('INSERT INTO math_concepts VALUES(?, ?)', (ident, name))
                for block in extract_all_pstricks_diagram_blocks(tex):
                    db.execute("INSERT INTO math_concept_diagrams VALUES(?, ?, 'd.svg')", (ident, block['source_hash']))
            db.commit()
        return str(path)

    def scan(self, baseline, working, svgs=None):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)/'base.db'
            base.write_bytes(b'baseline')
            local = self.working_db(temp, svgs or {})
            state = dict(base=str(base), base_sha256=helper.digest(base), working=local)
            snapshots = {str(base): baseline, local: working}
            with patch.object(helper, 'read_snapshot', side_effect=lambda path: snapshots[str(path)]):
                return {item['canonical']: item for item in helper.changed_entries(state)}

    def test_plain_text_and_new_entries_stay_supported(self):
        changes = self.scan({'MetricSpace': entry()},
                            {'MetricSpace': entry(cleaned_tex='A metric space is a set with a distance.'),
                             'NormedSpace': entry(slug='normed-space', title='normed space')})
        self.assertTrue(changes['MetricSpace']['supported'])
        self.assertIsNone(changes['MetricSpace']['reason'])
        self.assertTrue(changes['NormedSpace']['supported'])

    def test_existing_diagram_entry_is_editable_only_around_stored_diagrams(self):
        tex = 'See the figure.\n' + PICTURE
        baseline = {'Stored': entry(cleaned_tex=tex), 'NoSvg': entry(cleaned_tex=tex), 'Changed': entry(cleaned_tex=tex),
                    'Image': entry(cleaned_tex='\\includegraphics{x.png}')}
        working = {'Stored': entry(cleaned_tex='Edited. ' + tex), 'NoSvg': entry(cleaned_tex='Edited. ' + tex),
                   'Changed': entry(cleaned_tex=tex.replace('(1,1)', '(2,2)')),
                   'Image': entry(cleaned_tex='Edited. \\includegraphics{x.png}')}
        changes = self.scan(baseline, working, svgs={'Stored': tex, 'Changed': tex})
        self.assertIsNone(changes['Stored']['reason'])
        self.assertIsNone(changes['Image']['reason'])
        self.assertIn('no stored SVG', changes['NoSvg']['reason'])
        # A changed diagram now takes the diagram route, which needs its new SVG rendered first.
        self.assertTrue(changes['Changed']['diagrams'])
        self.assertIn('choose 19 to render them', changes['Changed']['reason'])

    def test_missing_classification_and_duplicate_metadata_no_longer_block(self):
        changes = self.scan({'Percentile': entry(classifications=[]),
                             'Hypergroup': entry(definitions=['absolute identity', 'absolute identity'])},
                            {'Percentile': entry(classifications=[], cleaned_tex='Edited.'),
                             'Hypergroup': entry(definitions=['absolute identity', 'absolute identity'],
                                                 cleaned_tex='Edited.')})
        self.assertTrue(changes['Percentile']['supported'])
        self.assertTrue(changes['Hypergroup']['supported'])

    def test_local_edit_that_adds_media_or_bad_synonyms_is_flagged(self):
        changes = self.scan({'A': entry(), 'B': entry(), 'C': entry()},
                            {'A': entry(cleaned_tex='Text \\includegraphics{x.png}'),
                             'B': entry(synonyms=['Distance space', 'distance space']),
                             'C': entry(cleaned_tex=' ')})
        self.assertTrue(changes['A']['reason'].startswith('local version adds, removes or changes a diagram'))
        self.assertIn('differs only in capitalization', changes['B']['reason'])
        self.assertEqual(changes['C']['reason'], 'local version has empty content')

    def test_other_field_changes_deletions_and_bad_new_entries(self):
        changes = self.scan({'A': entry(), 'Gone': entry()},
                            {'A': entry(types=['Theorem']),
                             "Euler'stheorem": entry(slug="euler'stheorem")})
        self.assertIn('changes types; only content and synonym changes', changes['A']['reason'])
        self.assertIn('deletions are not supported', changes['Gone']['reason'])
        self.assertIn('new entry slug', changes["Euler'stheorem"]['reason'])

    def test_option_2_refuses_with_the_same_reason(self):
        candidate = dict(canonical='Deduction', supported=False, new=False,
                         reason='has 1 diagram(s) with no stored SVG')
        with patch.object(helper, 'changed_entries', return_value=[candidate]):
            with self.assertRaisesRegex(ValueError, 'has 1 diagram\\(s\\) with no stored SVG'):
                helper.prepare_selected({}, 'Deduction')

    def test_option_1_agrees_with_the_option_2_preparers(self):
        baseline = {'Text': entry(), 'Diagram': entry(cleaned_tex=PICTURE), 'NoSvg': entry(cleaned_tex=PICTURE),
                    'ChangedDiagram': entry(cleaned_tex=PICTURE), 'Unclassified': entry(classifications=[]),
                    'Untyped': entry(types=[]), 'Duplicate': entry(synonyms=['ring', 'ring']),
                    'Synonyms': entry(), 'CaseSynonyms': entry(), 'AddsImage': entry(), 'Empty': entry()}
        working = {'Text': entry(cleaned_tex='Edited.'), 'Diagram': entry(cleaned_tex=PICTURE + ' Edited.'),
                   'NoSvg': entry(cleaned_tex=PICTURE + ' Edited.'),
                   'ChangedDiagram': entry(cleaned_tex=PICTURE.replace('(1,1)', '(2,2)')),
                   'Unclassified': entry(classifications=[], cleaned_tex='Edited.'),
                   'Untyped': entry(types=[], cleaned_tex='Edited.'),
                   'Duplicate': entry(synonyms=['ring', 'ring'], cleaned_tex='Edited.'),
                   'Synonyms': entry(synonyms=['distance space', 'metric']),
                   'CaseSynonyms': entry(synonyms=['Metric', 'metric']),
                   'AddsImage': entry(cleaned_tex='<img src="x.png">'),
                   'Empty': entry(cleaned_tex=''),
                   'NewText': entry(slug='new-text', title='new text'),
                   'NewDiagram': entry(slug='new-diagram', title='new diagram', cleaned_tex=PICTURE),
                   'NewBadSlug': entry(slug='New_Slug', title='new slug'),
                   'NewUnclassified': entry(slug='new-unclassified', title='new unclassified', classifications=[])}
        svgs = {'Diagram': PICTURE, 'ChangedDiagram': PICTURE}
        changes = self.scan(baseline, working, svgs)
        self.assertEqual(set(changes), set(working))
        with tempfile.TemporaryDirectory() as temp, \
             patch.object(prepare_math_patch, 'read_snapshot', side_effect=lambda path: baseline if path == 'b' else working):
            local = self.working_db(temp, svgs)
            for name, item in changes.items():
                with self.subTest(name):
                    try:
                        if item['new']:
                            helper.validate_entry(dict(working[name], canonical_name=name))
                        else:
                            prepare_math_patch.prepare('b', local, name, Path(temp)/(name + '.zip'))
                        accepted = True
                    except ValueError:
                        accepted = False
                    self.assertEqual(item['supported'], accepted, item['reason'])
        self.assertEqual({name for name, item in changes.items() if item['supported']},
                         {'Text', 'Diagram', 'Unclassified', 'Untyped', 'Duplicate', 'Synonyms', 'NewText'})


if __name__ == '__main__':
    unittest.main()
