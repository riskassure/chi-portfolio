"""Retirement contract 1: how every website reader treats retired math entries.

services/math/retirement.py declares RETIREMENT_CONTRACT. This suite is what
that number means; code may declare contract 1 only while all of it passes.
The helper refuses to deploy code declaring less than the live database
needs, and refuses to publish a retirement before the website declares it.
"""
from contextlib import closing
import json
from pathlib import Path
import re
import sqlite3
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

from flask import Flask

sys.path.insert(0, str(Path(__file__).resolve().parent))
from math_fixture import make_catalog, merge_by_hand, retire_by_hand  # noqa: E402
from services.math import retirement  # noqa: E402
from services.math.autolink_service import apply_math_autolinker  # noqa: E402
from services.math.public_catalog_service import fetch_public_math_catalog  # noqa: E402
from services.math.public_concept_detail_service import fetch_public_math_concept_detail  # noqa: E402
from services.math.public_search_service import search_public_math_library  # noqa: E402
from services.math.slug_helper import new_entry_names  # noqa: E402

CONTRACT_CHECKED = 1


def hrefs(html):
    return re.findall(r'href="concept\.html\?slug=([^"]+)"', html)


class Catalog(unittest.TestCase):
    upgraded = True

    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.path = Path(temp.name) / 'math.db'
        self.ids = make_catalog(self.path, upgraded=self.upgraded)

    def cursor(self):
        db = sqlite3.connect(self.path)
        db.row_factory = sqlite3.Row
        self.addCleanup(db.close)
        return db.cursor()

    def detail(self, identifier):
        return fetch_public_math_concept_detail(self.cursor(), identifier)

    def client(self):
        fake_app = types.ModuleType('app')
        fake_app.admin_required = lambda view: view
        modules = patch.dict(sys.modules, {'app': fake_app})
        modules.start()
        self.addCleanup(modules.stop)
        from routes import admin_math
        database = patch.object(admin_math, 'DB_PATH', self.path)
        database.start()
        self.addCleanup(database.stop)
        app = Flask(__name__)
        app.register_blueprint(admin_math.math_bp)
        return app.test_client()


class ContractOneTests(Catalog):
    """A merged entry (monoid with inverses into group) and a plain retirement (old stub)."""

    def setUp(self):
        super().setUp()
        merge_by_hand(self.path, self.ids['monoid with inverses'], self.ids['group'])
        retire_by_hand(self.path, self.ids['old stub'], reason='unfinished test entry')

    def test_this_suite_defines_the_declared_contract(self):
        self.assertEqual(retirement.RETIREMENT_CONTRACT, CONTRACT_CHECKED)

    def test_old_url_by_slug_or_id_shows_the_survivor(self):
        for identifier in ('monoid-with-inverses', str(self.ids['monoid with inverses'])):
            page = self.detail(identifier)
            self.assertEqual(page['slug'], 'group')
            self.assertEqual(page['merged_from'], {'title': 'monoid with inverses', 'slug': 'monoid-with-inverses'})
            self.assertIn('display_tex', page)

    def test_redirects_into_a_retired_entry_reach_its_survivor(self):
        with closing(sqlite3.connect(self.path)) as db:
            db.execute("INSERT INTO math_concepts(canonical_name, slug, title, cleaned_tex) VALUES "
                       "('EarlierDraft', 'earlier-draft', 'earlier draft', 'x')")
            db.commit()
            draft = db.execute("SELECT id FROM math_concepts WHERE slug='earlier-draft'").fetchone()[0]
        retire_by_hand(self.path, draft, into=self.ids['monoid with inverses'])
        self.assertEqual(self.detail('earlier-draft')['slug'], 'group')

    def test_plain_retirement_shows_only_a_notice(self):
        page = self.detail('old-stub')
        self.assertTrue(page['retired'])
        self.assertEqual(page['retirement_reason'], 'unfinished test entry')
        self.assertNotIn('display_tex', page)

    def test_an_active_page_is_unchanged_apart_from_redirected_links(self):
        page = self.detail('subgroup')
        self.assertNotIn('merged_from', page)
        self.assertEqual([item['slug'] for item in page['related_concepts']], ['group'])
        links = hrefs(page['display_tex'])
        self.assertIn('group', links)
        self.assertNotIn('monoid-with-inverses', links)
        self.assertNotIn('old-stub', links)
        self.assertIn('the stub', page['display_tex'])  # Visible text stays, without its link.

    def test_autolinker_uses_the_survivor_and_skips_retired_entries(self):
        html = apply_math_autolinker(-1, 'A monoid with inverses has an inverse element; see old stub.', self.cursor())
        self.assertEqual(hrefs(html), ['group', 'group'])

    def test_catalog_and_classification_lists_show_active_entries_only(self):
        slugs = {row['slug'] for row in fetch_public_math_catalog(self.cursor())}
        self.assertEqual(slugs, {'group', 'subgroup'})
        self.assertEqual(fetch_public_math_catalog(self.cursor(), classification_filter='99Z99'), [])
        codes = [row['code'] for row in self.client().get('/api/math/classifications').json['data']]
        self.assertEqual(codes, ['20A05'])

    def test_search_finds_the_survivor_by_the_old_title_and_never_a_retired_entry(self):
        def concepts(query):
            rows = search_public_math_library(self.cursor(), query)['data']
            return [row['slug'] for row in rows if row['kind'] == 'concept']
        self.assertEqual(concepts('monoid with inverses'), ['group'])
        self.assertEqual(concepts('old stub'), [])

    def test_admin_lists_retired_entries_as_retired_and_refuses_to_edit_them(self):
        client = self.client()
        rows = client.get('/api/admin/math/concepts/search?q=stub').json['data']
        self.assertEqual([(row['slug'], row['retired']) for row in rows], [('old-stub', True)])
        detail = client.get(f"/api/admin/math/concepts/{self.ids['old stub']}").json['data']
        self.assertEqual(detail['retirement']['retirement_reason'], 'unfinished test entry')
        self.assertIsNone(client.get(f"/api/admin/math/concepts/{self.ids['group']}").json['data']['retirement'])
        refused = client.post('/api/admin/math/update', json=dict(
            id=self.ids['old stub'], title='old stub', cleaned_tex='Edited.'))
        self.assertEqual(refused.status_code, 409)
        with closing(sqlite3.connect(self.path)) as db:
            text = db.execute('SELECT cleaned_tex FROM math_concepts WHERE id = ?', (self.ids['old stub'],)).fetchone()
        self.assertEqual(text[0], 'Unfinished.')

    def test_new_entries_keep_retired_names_and_urls_reserved_but_not_their_titles(self):
        cursor = self.cursor()
        with self.assertRaisesRegex(ValueError, "slug 'old-stub' is already used"):
            new_entry_names(cursor, 'old stub')
        self.assertEqual(new_entry_names(cursor, 'old stub', 'old-stub-revisited'),
                         ('OldStubRevisited', 'old-stub-revisited'))
        # The merged title now belongs to the survivor as a synonym.
        with self.assertRaisesRegex(ValueError, "synonym of 'group'"):
            new_entry_names(cursor, 'monoid with inverses', 'other-slug')


class NoRetirementsTests(Catalog):
    """With no retirements, an upgraded database reads exactly like one before the upgrade."""

    upgraded = False

    def readings(self):
        cursor = self.cursor()
        result = {'catalog': fetch_public_math_catalog(cursor),
                  'search': search_public_math_library(cursor, 'group'),
                  'autolink': apply_math_autolinker(-1, 'A monoid with inverses and an old stub.', cursor)}
        for slug in ('group', 'monoid-with-inverses', 'old-stub', 'subgroup'):
            result[slug] = fetch_public_math_concept_detail(cursor, slug)
        result['classifications'] = self.client().get('/api/math/classifications').json
        return json.loads(json.dumps(result))

    def test_upgrade_changes_no_public_reading(self):
        before = self.readings()
        with closing(sqlite3.connect(self.path)) as db:
            import math_schema
            db.execute('BEGIN')
            math_schema.upgrade(db)
            db.commit()
        self.assertEqual(self.readings(), before)


if __name__ == '__main__':
    unittest.main()
