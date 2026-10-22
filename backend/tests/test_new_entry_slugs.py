from contextlib import closing
import json
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

from flask import Flask

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND / 'src'))
sys.path.insert(0, str(BACKEND))
from services.math import slug_helper
from services.math import concept_update_service
from publish_math_entry import validate as publisher_validate

EDITOR_JS = BACKEND.parent / 'frontend' / 'math' / 'math_editor.js'

TITLES = {
    'metric space': ('metric-space', 'MetricSpace'),
    'Metric Space': ('metric-space', 'MetricSpace'),
    "Euler's theorem": ('eulers-theorem', 'EulersTheorem'),
    'Euler’s theorem': ('eulers-theorem', 'EulersTheorem'),
    'Abel–Ruffini theorem': ('abel-ruffini-theorem', 'AbelRuffiniTheorem'),
    'Sylow theorems (first)': ('sylow-theorems-first', 'SylowTheoremsFirst'),
    'Gödel  numbering': ('godel-numbering', 'GodelNumbering'),
    ' L^p space ': ('l-p-space', 'LPSpace'),
}

# Pinned output of the historical generator. Existing URLs came from it via
# the PlanetMath import, so it must keep producing exactly these.
HISTORICAL = {
    'MetricSpace': 'metric-space',
    'ProofOfFermatsLittleTheorem': 'proof-of-fermats-little-theorem',
    'Monic': 'monic',
    'CategoryOfSets': 'category-of-sets',
    'LpSpace': 'lp-space',
    'GCD': 'gcd',
    'AxiomOfChoice_Equivalents': 'axiom-of-choice-equivalents',
}

SCHEMA = '''
CREATE TABLE math_concepts(id INTEGER PRIMARY KEY AUTOINCREMENT, canonical_name TEXT NOT NULL UNIQUE,
    slug TEXT NOT NULL, title TEXT, owner TEXT, cleaned_tex TEXT, rendered_tex TEXT, is_cleaned INTEGER,
    created_at TEXT, updated_at TEXT);
INSERT INTO math_concepts(canonical_name, slug, title, cleaned_tex) VALUES
    ('MetricSpace', 'metric-space', 'metric space', 'A metric space.'),
    ('Monic', 'monomorphism', 'monomorphism', 'A monic arrow.'),
    ('Metricspace', 'metricspace', 'metricspace', 'Made by the old editor rule.');
'''


def make_db(path):
    with closing(sqlite3.connect(path)) as db:
        db.executescript(SCHEMA)
        db.commit()


def rows(path):
    with closing(sqlite3.connect(path)) as db:
        return db.execute('SELECT id, canonical_name, slug, title FROM math_concepts ORDER BY id').fetchall()


class SlugRuleTests(unittest.TestCase):
    def test_titles_become_lowercase_hyphenated_slugs(self):
        for title, (slug, canonical) in TITLES.items():
            with self.subTest(title=title):
                self.assertEqual(slug_helper.slug_from_title(title), slug)
                self.assertEqual(slug_helper.canonical_from_slug(slug), canonical)

    def test_generated_slugs_pass_the_publisher(self):
        for title, (slug, canonical) in TITLES.items():
            entry = dict(canonical_name=canonical, slug=slug, title=title, owner='CWoo', cleaned_tex='Text.',
                         is_cleaned=1, classifications=['54E35'], types=['Definition'], synonyms=[],
                         definitions=[], link_exclusions=[], related_concepts=[])
            publisher_validate(entry)

    def test_slug_pattern_matches_the_publisher(self):
        source = (BACKEND / 'publish_math_entry.py').read_text(encoding='utf-8')
        self.assertIn(f"re.fullmatch(r'{slug_helper.NEW_SLUG_PATTERN.pattern}'", source)

    def test_historical_generator_is_unchanged(self):
        for canonical, slug in HISTORICAL.items():
            self.assertEqual(slug_helper.generate_slug(canonical), slug)

    def test_editor_preview_uses_the_same_rule(self):
        node = shutil.which('node')
        if not node:
            self.skipTest('node is not installed')
        source = EDITOR_JS.read_text(encoding='utf-8')
        function = re.search(r'^function slugFromTitle\(title\) \{.*?^\}', source, re.S | re.M).group(0)
        script = function + '\nconsole.log(JSON.stringify(%s.map(slugFromTitle)));' % json.dumps(list(TITLES))
        output = subprocess.run([node, '-e', script], capture_output=True, text=True, check=True).stdout
        self.assertEqual(json.loads(output), [slug for slug, _ in TITLES.values()])


class NewEntryNameTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.db = Path(temp.name) / 'math.db'
        make_db(self.db)

    def names(self, title, slug=None):
        with closing(sqlite3.connect(self.db)) as db:
            return slug_helper.new_entry_names(db.cursor(), title, slug)

    def test_derived_and_requested_slugs(self):
        self.assertEqual(self.names('Normed space'), ('NormedSpace', 'normed-space'))
        self.assertEqual(self.names('kernels and cokernels of module homomorphisms', 'module-kernels'),
                         ('ModuleKernels', 'module-kernels'))
        self.assertEqual(self.names('Normed space', '  '), ('NormedSpace', 'normed-space'))

    def test_unsuitable_slugs_are_rejected(self):
        for slug in ['Metric-Space', 'metric space', "euler's", 'metric--space', '-metric', 'abel–ruffini']:
            with self.subTest(slug=slug), self.assertRaisesRegex(ValueError, 'lowercase'):
                self.names('anything', slug)
        with self.assertRaisesRegex(ValueError, 'no letters or digits'):
            self.names('∞')

    def test_duplicates_are_rejected_case_insensitively(self):
        with self.assertRaisesRegex(ValueError, "slug 'metric-space' is already used by 'metric space'"):
            self.names('Metric Space')
        with self.assertRaisesRegex(ValueError, "canonical name 'Monic'"):
            self.names('monic')
        with self.assertRaisesRegex(ValueError, 'already used'):
            self.names('another title', 'monomorphism')


class CreateRouteTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.db = Path(temp.name) / 'math.db'
        make_db(self.db)
        fake_app = types.ModuleType('app')
        fake_app.admin_required = lambda view: view
        patcher = patch.dict(sys.modules, {'app': fake_app})
        patcher.start()
        self.addCleanup(patcher.stop)
        from routes import admin_math
        self.created = []

        def create(cursor, canonical_name, slug, title, **_):
            cursor.execute('INSERT INTO math_concepts(canonical_name, slug, title) VALUES(?, ?, ?)',
                           (canonical_name, slug, title))
            self.created.append((canonical_name, slug))
            return {'concept_id': cursor.lastrowid, 'slug': slug}

        for item in [patch.object(admin_math, 'DB_PATH', self.db),
                     patch.object(admin_math, 'create_math_concept', side_effect=create)]:
            item.start()
            self.addCleanup(item.stop)
        app = Flask(__name__)
        app.register_blueprint(admin_math.math_bp)
        self.client = app.test_client()

    def post(self, **body):
        return self.client.post('/api/admin/math/create', json=dict(cleaned_tex='Some text.', **body))

    def test_lowercase_title_gets_hyphenated_slug(self):
        result = self.post(title="Euler's theorem")
        self.assertEqual(result.status_code, 201)
        self.assertEqual(result.json['slug'], 'eulers-theorem')
        self.assertEqual(self.created, [('EulersTheorem', 'eulers-theorem')])

    def test_requested_slug_is_used(self):
        result = self.post(title='kernels and cokernels of module homomorphisms', slug='module-kernels-and-cokernels')
        self.assertEqual(result.status_code, 201)
        self.assertEqual(self.created, [('ModuleKernelsAndCokernels', 'module-kernels-and-cokernels')])

    def test_rejected_before_saving_and_existing_rows_untouched(self):
        before = rows(self.db)
        for body in [dict(title='metric space'), dict(title='x', slug='Bad Slug'), dict(title='∞')]:
            with self.subTest(body=body):
                result = self.post(**body)
                self.assertEqual(result.status_code, 400)
                self.assertFalse(result.json['success'])
                self.assertTrue(result.json['message'])
        self.assertEqual(self.created, [])
        self.assertEqual(rows(self.db), before)

    def test_creating_leaves_existing_entries_alone(self):
        before = rows(self.db)
        self.assertEqual(self.post(title='normed space').status_code, 201)
        self.assertEqual(rows(self.db)[:len(before)], before)


class ExistingEntryTests(unittest.TestCase):
    def test_editing_an_entry_keeps_its_slug_and_canonical_name(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'math.db'
            make_db(path)
            with closing(sqlite3.connect(path)) as db, \
                    patch.object(concept_update_service, 'render_tex_reusing_existing_diagrams', return_value='<p>x</p>'), \
                    patch.object(concept_update_service, 'replace_concept_metadata'):
                result = concept_update_service.update_math_concept(
                    cursor=db.cursor(), concept_id=3, updated_title='Metric space (old rule)', updated_owner='CWoo',
                    updated_tex='Made by the old editor rule.', updated_at='2026-10-22 00:00:00', is_cleaned_flag=1,
                    classifications=[], types=[], synonyms=[], definitions=[], related_concepts=[])
                db.commit()
            self.assertEqual(result['slug'], 'metricspace')
            self.assertEqual(rows(path)[2], (3, 'Metricspace', 'metricspace', 'Metric space (old rule)'))


if __name__ == '__main__':
    unittest.main()
