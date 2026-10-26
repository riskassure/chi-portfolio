from contextlib import closing
import csv
import hashlib
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import find_merge_candidates as finder

SCHEMA = '''
CREATE TABLE math_concepts(id INTEGER PRIMARY KEY, canonical_name TEXT UNIQUE, slug TEXT, title TEXT, cleaned_tex TEXT);
CREATE TABLE math_classifications(id INTEGER PRIMARY KEY, code TEXT);
CREATE TABLE math_types(id INTEGER PRIMARY KEY, type_name TEXT);
CREATE TABLE math_concept_classifications(concept_id INTEGER, classification_id INTEGER);
CREATE TABLE math_concept_types(concept_id INTEGER, type_id INTEGER);
CREATE TABLE math_synonyms(concept_id INTEGER, synonym_text TEXT);
CREATE TABLE math_definitions(concept_id INTEGER, defined_term TEXT);
CREATE TABLE math_related_concepts(concept_id INTEGER, related_canonical_name TEXT, related_concept_id INTEGER);
'''
# Long enough for several distinct four-word shingles.
SHARED = ('Let G be a group acting on a set X and suppose every orbit of the action is finite '
          'then the number of orbits equals the average number of points fixed by an element of G '
          'which is the statement usually called the orbit counting lemma in combinatorics')
# Distinct endings that keep two entries well short of a near-subset.
FULL = ' the functor is full when each map between hom sets is surjective for every pair of objects in the category'
FAITHFUL = ' the functor is faithful when every induced map on morphisms is injective so distinct arrows stay distinct'


class Catalog:
    """A small math catalog in a temporary file, built entry by entry."""

    def __init__(self, folder, retirement=False):
        self.path = Path(folder) / 'working.db'
        self.db = sqlite3.connect(self.path)
        self.db.executescript(SCHEMA)
        if retirement:
            self.db.execute('ALTER TABLE math_concepts ADD COLUMN retired_at TEXT')
        self.next_id = 1

    def add(self, title, tex, msc=('20B05',), types=('Definition',), synonyms=(), definitions=(), related=(),
            retired=False):
        ident = self.next_id
        self.next_id += 1
        canonical = ''.join(word.capitalize() for word in title.split()) + str(ident)
        self.db.execute('INSERT INTO math_concepts(id, canonical_name, slug, title, cleaned_tex) VALUES(?,?,?,?,?)',
                        (ident, canonical, title.lower().replace(' ', '-') + str(ident), title, tex))
        if retired:
            self.db.execute('UPDATE math_concepts SET retired_at = ? WHERE id = ?', ('2026-10-25T00:00:00Z', ident))
        for code in msc:
            row = self.db.execute('SELECT id FROM math_classifications WHERE code = ?', (code,)).fetchone()
            cid = row[0] if row else self.db.execute('INSERT INTO math_classifications(code) VALUES(?)', (code,)).lastrowid
            self.db.execute('INSERT INTO math_concept_classifications VALUES(?,?)', (ident, cid))
        for name in types:
            row = self.db.execute('SELECT id FROM math_types WHERE type_name = ?', (name,)).fetchone()
            tid = row[0] if row else self.db.execute('INSERT INTO math_types(type_name) VALUES(?)', (name,)).lastrowid
            self.db.execute('INSERT INTO math_concept_types VALUES(?,?)', (ident, tid))
        self.db.executemany('INSERT INTO math_synonyms VALUES(?,?)', [(ident, s) for s in synonyms])
        self.db.executemany('INSERT INTO math_definitions VALUES(?,?)', [(ident, d) for d in definitions])
        for other in related:
            name = self.db.execute('SELECT canonical_name FROM math_concepts WHERE id = ?', (other,)).fetchone()[0]
            self.db.execute('INSERT INTO math_related_concepts VALUES(?,?,?)', (ident, name, other))
        self.db.commit()
        return ident

    def rows(self):
        with closing(sqlite3.connect(self.path.as_uri() + '?mode=ro', uri=True)) as db:
            return finder.find_candidates(finder.load(db))

    def close(self):
        self.db.close()


def pair(rows, a, b):
    found = [r for r in rows if {r['a']['id'], r['b']['id']} == {a, b}]
    return found[0] if found else None


class CandidateTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.catalog = Catalog(self.folder.name)

    def tearDown(self):
        self.catalog.close()
        self.folder.cleanup()

    def test_same_title_in_different_subjects_is_a_rename(self):
        a = self.catalog.add('filtration', 'A filtration of a module.', msc=('13A99',))
        b = self.catalog.add('filtration', 'A filtration in modal logic.', msc=('03B45',))
        self.assertEqual(pair(self.catalog.rows(), a, b)['action'], 'rename')

    def test_same_title_and_area_without_shared_text_is_not_a_merge(self):
        a = self.catalog.add('Burnside lemma', 'Short text about orbits.', msc=('20B05',))
        b = self.catalog.add('Burnside lemma', 'Entirely different words describing another idea.', msc=('20B99',))
        row = pair(self.catalog.rows(), a, b)
        self.assertEqual(row['action'], 'rename')
        self.assertIn('read both', row['reason'])

    def test_same_title_with_strong_overlap_is_a_merge_and_the_linked_entry_survives(self):
        a = self.catalog.add('Burnside lemma', SHARED + FULL, msc=('20B05',))
        b = self.catalog.add('Burnside lemma', SHARED + FAITHFUL, msc=('20B99',))
        self.catalog.add('group action', 'Groups act.', related=(a,))
        row = pair(self.catalog.rows(), a, b)
        self.assertEqual(row['action'], 'merge')
        self.assertIn('strong text overlap', row['reason'])
        self.assertTrue(row['survivor'].endswith(f'({a})'))

    def test_a_short_same_title_entry_sharing_some_wording_is_a_possible_stub(self):
        unfinished = ' '.join(SHARED.split()[:20]) + ' ' + ' '.join(f'draft{i}' for i in range(20))
        complete = SHARED + ' ' + ' '.join(f'step{i}' for i in range(300))
        a = self.catalog.add('Burnside lemma', unfinished, msc=('20B05',))
        b = self.catalog.add('Burnside lemma', complete, msc=('20B05',))
        row = pair(self.catalog.rows(), a, b)
        self.assertEqual(row['action'], 'merge')
        self.assertIn('stub', row['reason'])

    def test_shared_terminology_alone_never_suggests_a_merge(self):
        a = self.catalog.add('order ideal', 'One text.', synonyms=('ideal',), definitions=('down set',))
        b = self.catalog.add('lattice ideal', 'Another text.', synonyms=('ideal',), definitions=('down set',))
        row = pair(self.catalog.rows(), a, b)
        self.assertEqual(row['signals'], ['shared alias'])
        self.assertEqual(row['action'], 'leave')

    def test_templated_sibling_definitions_are_cross_linked_not_merged(self):
        a = self.catalog.add('full functor', SHARED + FULL, msc=('18A22',))
        b = self.catalog.add('faithful functor', SHARED + FAITHFUL, msc=('18A22',))
        self.assertLess(pair(self.catalog.rows(), a, b)['containment'], finder.NEAR_SUBSET)
        self.assertEqual(pair(self.catalog.rows(), a, b)['action'], 'cross-link')

    def test_already_linked_siblings_are_left_alone(self):
        a = self.catalog.add('full functor', SHARED + FULL, msc=('18A22',))
        b = self.catalog.add('faithful functor', SHARED + FAITHFUL, msc=('18A22',), related=(a,))
        self.assertEqual(pair(self.catalog.rows(), a, b)['action'], 'leave')

    def test_near_subset_in_the_same_area_is_a_merge(self):
        a = self.catalog.add('orbit counting lemma', SHARED)
        b = self.catalog.add('Cauchy-Frobenius lemma', SHARED + ' with a proof by double counting')
        row = pair(self.catalog.rows(), a, b)
        self.assertEqual(row['action'], 'merge')
        self.assertGreaterEqual(row['containment'], finder.NEAR_SUBSET)

    def test_a_proof_and_its_statement_are_cross_linked(self):
        a = self.catalog.add('orbit counting lemma', SHARED, types=('Theorem',))
        b = self.catalog.add('proof of orbit counting lemma', SHARED + ' proof follows', types=('Proof',))
        row = pair(self.catalog.rows(), a, b)
        self.assertEqual(row['action'], 'cross-link')
        self.assertIn('different roles', row['reason'])

    def test_retired_entries_are_not_candidates(self):
        self.catalog.close()
        self.folder.cleanup()
        self.folder = tempfile.TemporaryDirectory()
        self.catalog = Catalog(self.folder.name, retirement=True)
        a = self.catalog.add('Burnside lemma', 'Short.')
        b = self.catalog.add('Burnside lemma', 'Longer.', retired=True)
        self.assertIsNone(pair(self.catalog.rows(), a, b))


class ReportTests(unittest.TestCase):
    def test_report_is_written_without_changing_the_database(self):
        with tempfile.TemporaryDirectory() as folder:
            catalog = Catalog(folder)
            catalog.add('filtration', 'A filtration of a module.', msc=('13A99',))
            catalog.add('filtration', 'A filtration in modal logic.', msc=('03B45',))
            catalog.close()
            before = hashlib.sha256(catalog.path.read_bytes()).hexdigest()
            output = Path(folder) / 'report'
            _, counts = finder.run(catalog.path, output)
            self.assertEqual(hashlib.sha256(catalog.path.read_bytes()).hexdigest(), before)
            self.assertEqual(counts['rename'], 1)
            text = (output / 'candidates.md').read_text(encoding='utf-8')
            self.assertIn('Heuristic', text)
            # Option 21 asks for canonical names, which older slugs don't always give.
            self.assertIn('filtration1, Filtration1;', text)
            with (output / 'candidates.csv').open(encoding='utf-8') as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(rows[0]['suggested_action (heuristic)'], 'rename')
            self.assertEqual(rows[0]['chi_decision'], '')
            self.assertEqual({rows[0]['canonical_a'], rows[0]['canonical_b']}, {'Filtration1', 'Filtration2'})
            with self.assertRaises(FileExistsError):
                finder.run(catalog.path, output)


if __name__ == '__main__':
    unittest.main()
