"""Exercise public search ranking and limits against an isolated SQLite catalog."""
from pathlib import Path
import sqlite3
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from services.math.public_search_service import search_public_math_library


class PublicSearchTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        self.db.row_factory = sqlite3.Row
        self.addCleanup(self.db.close)
        self.db.executescript('''
            CREATE TABLE math_concepts(id INTEGER PRIMARY KEY, title TEXT, slug TEXT, canonical_name TEXT);
            CREATE TABLE math_synonyms(concept_id INTEGER, synonym_text TEXT);
            CREATE TABLE math_definitions(concept_id INTEGER, defined_term TEXT);
            CREATE TABLE math_classifications(id INTEGER PRIMARY KEY, code TEXT, text TEXT, description TEXT);
            CREATE TABLE math_concept_classifications(concept_id INTEGER, classification_id INTEGER);
            INSERT INTO math_classifications VALUES(1, '20D20', 'Sylow subgroups', 'Finite group theory');
        ''')

    def entry(self, title, slug, canonical=''):
        return self.db.execute('INSERT INTO math_concepts(title,slug,canonical_name) VALUES(?,?,?)',
                               (title, slug, canonical)).lastrowid

    def search(self, query, **kwargs):
        return search_public_math_library(self.db.cursor(), query, **kwargs)['data']

    def concepts(self, query, **kwargs):
        return [row for row in self.search(query, **kwargs) if row['kind'] == 'concept']

    def test_reversed_words_and_partial_words_require_all_terms(self):
        self.entry('Sylow theorems', 'sylow-theorems', 'SylowTheorems')
        self.entry('Other theorem', 'other-theorem')
        self.assertEqual([r['slug'] for r in self.concepts('theor sylow')], ['sylow-theorems'])
        self.assertEqual(self.concepts('sylow missing'), [])

    def test_exact_title_then_phrase_then_reordered_then_aliases(self):
        exact = self.entry('Sylow theorem', 'exact')
        self.entry('Sylow theorem proof', 'prefix')
        self.entry('A Sylow theorem', 'phrase')
        self.entry('A theorem of Sylow', 'reordered')
        alias = self.entry('A group result', 'alias')
        definition = self.entry('A finite result', 'definition')
        self.db.execute('INSERT INTO math_synonyms VALUES(?,?)', (alias, 'Sylow theorem'))
        self.db.execute('INSERT INTO math_definitions VALUES(?,?)', (definition, 'Sylow theorem'))
        self.db.execute('INSERT INTO math_concept_classifications VALUES(?,1)', (exact,))
        rows = self.concepts('Sylow theorem')
        self.assertEqual([r['slug'] for r in rows], ['exact', 'prefix', 'phrase', 'reordered', 'alias', 'definition'])
        self.assertEqual(rows[0]['classification_codes'], ['20D20'])
        self.assertEqual(rows[-2]['match_type'], 'synonym')
        self.assertEqual(rows[-1]['matched_text'], 'Sylow theorem')

    def test_case_spaces_accents_apostrophes_and_dashes(self):
        self.entry("Euler’s theorem", 'eulers-theorem')
        self.entry('Abel–Ruffini theorem', 'abel-ruffini-theorem')
        self.entry('Gödel numbering', 'godel-numbering')
        for query, slug in [(" THEOREM   EULER'S ", 'eulers-theorem'),
                            ('ruffini, abel theorem', 'abel-ruffini-theorem'),
                            ('numbering GODEL', 'godel-numbering')]:
            with self.subTest(query=query):
                self.assertEqual([r['slug'] for r in self.concepts(query)], [slug])

    def test_aliases_do_not_consume_result_slots(self):
        first = self.entry('Alpha', 'alpha')
        second = self.entry('Beta', 'beta')
        for name in ['finite group', 'finite groups', 'groups finite']:
            self.db.execute('INSERT INTO math_synonyms VALUES(?,?)', (first, name))
        self.db.execute('INSERT INTO math_synonyms VALUES(?,?)', (second, 'finite group'))
        rows = self.concepts('group finite', concept_limit_value=2, explicit_family_limits=True)
        self.assertEqual([r['slug'] for r in rows], ['alpha', 'beta'])

    def test_empty_and_sql_wildcards_do_not_match_everything(self):
        self.entry('Group', 'group')
        for query in ['', '   ', '%_', '!!!', "' OR 1=1 --"]:
            self.assertEqual(self.search(query), [])

    def test_classifications_and_limits_keep_their_response_shape(self):
        for number in range(8):
            self.entry(f'Sylow result {number}', f'sylow-{number}')
        rows = self.search('sylow', overall_limit_value=4)
        self.assertEqual(len(rows), 4)
        self.assertEqual(rows[-1]['kind'], 'classification')
        self.assertEqual(self.search('theory finite')[0]['code'], '20D20')
        self.assertEqual(self.search('20D')[0]['code'], '20D20')
        rows = self.search('sylow', concept_limit_value=2, classification_limit_value=1,
                           explicit_family_limits=True)
        self.assertEqual(len(rows), 3)


if __name__ == '__main__':
    unittest.main()
