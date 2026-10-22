from contextlib import closing
import io
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from apply_math_text_patch import apply_patch, patch_intended
from inspect_staged_package import preview
from publish_math_entry import media_fragments
from services.math.render_helper import extract_all_pstricks_diagram_blocks

PICTURE = '\\psset{unit=1cm}\n\\begin{pspicture}(0,0)(2,2)\\psline(0,0)(2,2)\\end{pspicture}'
FIGURE = '\\begin{figure}\\includegraphics[width=3cm]{venn.png}\\caption{A Venn diagram}\\end{figure}'
TREE = '\\pstree{\\Tr{$A$}}{\\pstree{\\Tr{$B$}}{\\Tr{$C$}} \\Tr{$D$}}'


def stored(**changes):
    record = dict(slug='venn-diagram', title='Venn diagram', owner='chi', cleaned_tex='A Venn diagram.',
                  is_cleaned=1, classifications=['03E99'], types=['Definition'], synonyms=['set diagram'],
                  definitions=[], link_exclusions=[], related_concepts=[])
    record.update(changes)
    return record


def payload(expected, tex, synonyms=None):
    result = dict(canonical_name='VennDiagram', expected=expected, replacement_tex=tex)
    if synonyms is not None:
        result['replacement_synonyms'] = synonyms
    return result


class MediaFragmentTests(unittest.TestCase):
    def test_fragments_cover_whole_diagrams_and_ignore_prose(self):
        tex = 'Intro. ' + PICTURE + ' Middle. ' + FIGURE + ' Then ' + TREE + ' and <img src="a.png"> end.'
        self.assertEqual(media_fragments(tex),
                         ['\\psset{unit=1cm}', PICTURE.split('\n')[1], FIGURE, TREE, '<img src="a.png">'])
        edited = tex.replace('Intro.', 'A longer introduction.').replace('Middle.', 'Changed.')
        self.assertEqual(media_fragments(edited), media_fragments(tex))

    def test_any_edit_inside_a_diagram_changes_the_fragments(self):
        tex = 'Intro. ' + PICTURE + ' ' + FIGURE + ' ' + TREE
        for old, new in [('(2,2)\\end', '(3,3)\\end'), ('unit=1cm', 'unit=2cm'), ('A Venn', 'The Venn'),
                         ('$C$', '$E$'), ('venn.png', 'venn2.png')]:
            with self.subTest(old):
                self.assertNotEqual(media_fragments(tex.replace(old, new)), media_fragments(tex))
        self.assertEqual(media_fragments('No diagrams here.'), [])


class PatchRuleTests(unittest.TestCase):
    def test_unrelated_stored_metadata_no_longer_blocks_text_fixes(self):
        for name, expected in [('no classification', stored(classifications=[])),
                               ('no type', stored(types=[])),
                               ('duplicate definition', stored(definitions=['open segment', 'open segment'])),
                               ('old slug', stored(slug='examples-of-trees1')),
                               ('untrimmed related', stored(related_concepts=[' Set'])),
                               ('blank title', stored(title=''))]:
            with self.subTest(name):
                self.assertEqual(patch_intended(payload(expected, 'Fixed typo.')),
                                 dict(expected, cleaned_tex='Fixed typo.'))

    def test_unchanged_duplicate_synonyms_are_kept_and_changed_ones_must_be_clean(self):
        expected = stored(synonyms=['involutive ring', 'involutive ring'])
        self.assertEqual(patch_intended(payload(expected, 'Fixed.'))['synonyms'], ['involutive ring', 'involutive ring'])
        self.assertEqual(patch_intended(payload(expected, 'Fixed.', ['involutive ring']))['synonyms'], ['involutive ring'])
        for synonyms in (['a', 'a'], ['Ring', 'ring'], [' ring'], [''], 'ring', [3]):
            with self.subTest(synonyms):
                with self.assertRaises(ValueError):
                    patch_intended(payload(expected, 'Fixed.', synonyms))

    def test_text_around_unchanged_diagrams_can_change(self):
        tex = 'Before. ' + PICTURE + ' ' + FIGURE + ' After.'
        intended = patch_intended(payload(stored(cleaned_tex=tex), tex.replace('Before.', 'Rewritten opening.')))
        self.assertTrue(intended['cleaned_tex'].startswith('Rewritten opening.'))

    def test_added_removed_or_changed_diagrams_are_refused(self):
        tex = 'Before. ' + PICTURE + ' After.'
        for name, old, new in [('added to plain', 'A Venn diagram.', 'A Venn diagram. ' + FIGURE),
                               ('added second', tex, tex + ' ' + TREE),
                               ('removed', tex, 'Before. After.'),
                               ('changed', tex, tex.replace('(2,2)\\end', '(3,3)\\end')),
                               ('reordered', PICTURE + FIGURE, FIGURE + PICTURE),
                               ('embed added', 'Text.', 'Text. <iframe src="x"></iframe>')]:
            with self.subTest(name):
                with self.assertRaisesRegex(ValueError, 'Diagram or image changed'):
                    patch_intended(payload(stored(cleaned_tex=old), new))

    def test_image_changes_hidden_by_unusual_syntax_are_refused(self):
        cases = [('starred command', '\\includegraphics*{old.png}', '\\includegraphics*{new.png}'),
                 ('starred with options', '\\includegraphics*[width=2cm]{old.png}', '\\includegraphics*[width=2cm]{new.png}'),
                 ('quoted > in attribute', '<img alt="a > b" src="old.png">', '<img alt="a > b" src="new.png">'),
                 ("single-quoted '>'", "<img alt='>' src='old.png'>", "<img alt='>' src='new.png'>"),
                 ('self-closing svg', '<svg width="1"/> <img src="old.png">', '<svg width="1"/> <img src="new.png">'),
                 ('nested svg', '<svg><svg>a</svg><circle r="1"/></svg>', '<svg><svg>a</svg><circle r="2"/></svg>'),
                 ('plain TeX pspicture', '\\pspicture(0,0)(1,1)\\psline(0,0)(1,1)\\endpspicture',
                  '\\pspicture(0,0)(1,1)\\psline(0,0)(1,0)\\endpspicture'),
                 ('bare \\input', '\\input old.tex', '\\input new.tex'),
                 ('comment before argument', '\\includegraphics%\n{old.png}', '\\includegraphics%\n{new.png}')]
        for name, old, new in cases:
            with self.subTest(name):
                expected = stored(cleaned_tex='Before. ' + old + ' After.')
                with self.assertRaisesRegex(ValueError, 'Diagram or image changed'):
                    patch_intended(payload(expected, 'Before. ' + new + ' After.'))
                # The prose around the same fragment can still change.
                self.assertEqual(patch_intended(payload(expected, 'Edited. ' + old + ' After.'))['cleaned_tex'],
                                 'Edited. ' + old + ' After.')

    def test_empty_content_and_malformed_records_are_refused(self):
        for bad in (payload(stored(), '   '), payload(stored(), None), payload({'title': 'x'}, 'Text.'),
                    payload(stored(types=None), 'Text.'), dict(payload(stored(), 'Text.'), title='x')):
            with self.assertRaises(ValueError):
                patch_intended(bad)

    def test_staged_preview_accepts_an_unclassified_entry(self):
        data = io.BytesIO()
        with zipfile.ZipFile(data, 'w') as archive:
            archive.writestr('patch.json', json.dumps(payload(stored(classifications=[]), 'Fixed.')))
        self.assertIn('Proposed operation: change existing entry text', preview(data.getvalue()))


class ApplyDiagramEntryTests(unittest.TestCase):
    """Run the real server-side update on a diagram entry, with and without stored SVGs."""

    def database(self, root, tex, svg_for=None):
        database = root / 'live.db'
        with closing(sqlite3.connect(database)) as db:
            db.executescript('''
                CREATE TABLE math_concepts(id INTEGER PRIMARY KEY,canonical_name TEXT,slug TEXT,title TEXT,owner TEXT,cleaned_tex TEXT,is_cleaned INTEGER,rendered_tex TEXT,created_at TEXT,updated_at TEXT);
                CREATE TABLE math_classifications(id INTEGER PRIMARY KEY,code TEXT);
                CREATE TABLE math_types(id INTEGER PRIMARY KEY,type_name TEXT);
                CREATE TABLE math_concept_classifications(concept_id INTEGER,classification_id INTEGER);
                CREATE TABLE math_concept_types(concept_id INTEGER,type_id INTEGER);
                CREATE TABLE math_synonyms(concept_id INTEGER,synonym_text TEXT);
                CREATE TABLE math_definitions(concept_id INTEGER,defined_term TEXT);
                CREATE TABLE math_link_exclusions(concept_id INTEGER,word TEXT);
                CREATE TABLE math_related_concepts(concept_id INTEGER,related_canonical_name TEXT,related_concept_id INTEGER);
                CREATE TABLE math_concept_diagrams(id INTEGER PRIMARY KEY,concept_id INTEGER,block_index INTEGER,source_hash TEXT,source_tex TEXT,svg_path TEXT,created_at TEXT);
                INSERT INTO math_types VALUES(20,'Definition');
                INSERT INTO math_concept_types VALUES(1,20);
            ''')
            # No classification: the entry is in the "unclassified" group as well as the diagram group.
            db.execute("INSERT INTO math_concepts VALUES(1,'VennDiagram','venn-diagram','Venn diagram','chi',?,1,'old','t','t')", (tex,))
            for block in extract_all_pstricks_diagram_blocks(svg_for or ''):
                db.execute("INSERT INTO math_concept_diagrams VALUES(NULL,1,0,?,?,'diagrams/venn.svg','t')",
                           (block['source_hash'], block['conversion_source']))
            db.commit()
        return database

    def expected(self, tex):
        return stored(cleaned_tex=tex, classifications=[], synonyms=[])

    def test_text_edit_before_a_stored_diagram_is_applied_and_reuses_the_svg(self):
        tex = 'Before. ' + PICTURE + ' After.'
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            database = self.database(root, tex, svg_for=tex)
            new = tex.replace('Before.', 'A much longer opening sentence.')
            apply_patch(database, payload(self.expected(tex), new), root / 'backups',
                        Path(__file__).resolve().parents[1] / 'src')
            with closing(sqlite3.connect(database)) as db:
                cleaned, rendered = db.execute('SELECT cleaned_tex, rendered_tex FROM math_concepts').fetchone()
            self.assertEqual(cleaned, new)
            self.assertIn('venn.svg', rendered)
            self.assertNotIn('pspicture', rendered)

    def test_diagram_without_a_stored_svg_is_refused_before_backup(self):
        tex = 'Before. ' + TREE + ' After.'
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            database = self.database(root, tex)
            before = database.read_bytes()
            with self.assertRaisesRegex(ValueError, 'no stored SVG'):
                apply_patch(database, payload(self.expected(tex), tex.replace('After.', 'Later.')),
                            root / 'backups', Path(__file__).resolve().parents[1] / 'src')
            self.assertEqual(database.read_bytes(), before)
            self.assertFalse((root / 'backups').exists() and any((root / 'backups').iterdir()))


if __name__ == '__main__':
    unittest.main()
