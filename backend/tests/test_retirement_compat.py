"""The retirement schema upgrade leaves every existing helper path working.

Covers the upgrade itself (checked and idempotent), the snapshot every
package relies on, old-format packages on an upgraded database, the guards
that keep packages off retired entries, option 8 across the known upgrade,
and the website code contract guard.
"""
from contextlib import closing
import hashlib
import io
import json
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import Mock
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from math_fixture import make_catalog, merge_by_hand, retire_by_hand  # noqa: E402
import math_schema  # noqa: E402
from bring_changes_home import refresh  # noqa: E402
import frontend_sync  # noqa: E402
from inspect_staged_package import preview  # noqa: E402
from live_math_publication import publish  # noqa: E402
from preview_math_sync import read_snapshot, read_status  # noqa: E402

SOURCE = Path(__file__).resolve().parents[1] / 'src'


def zipped(name, payload):
    data = io.BytesIO()
    with zipfile.ZipFile(data, 'w') as archive:
        archive.writestr(name, json.dumps(payload))
    return data.getvalue()


def upgrade(path):
    with closing(sqlite3.connect(path)) as db:
        db.execute('BEGIN')
        statements = math_schema.upgrade(db)
        db.commit()
    return statements


class TempFolder(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)


class SchemaUpgradeTests(TempFolder):
    def setUp(self):
        super().setUp()
        self.path = self.root / 'math.db'
        make_catalog(self.path, upgraded=False)

    def test_upgrade_is_idempotent_and_states_are_reported(self):
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(math_schema.state(db), 'absent')
        self.assertEqual(len(upgrade(self.path)), 7)
        self.assertEqual(upgrade(self.path), [])
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(math_schema.state(db), 'current')
            self.assertEqual(math_schema.required_contract(db), 0)
            self.assertEqual(db.execute('PRAGMA integrity_check').fetchone()[0], 'ok')

    def test_partial_upgrade_is_completed(self):
        with closing(sqlite3.connect(self.path)) as db:
            db.execute(math_schema.COLUMN_SQL['retired_at'])
            db.commit()
            self.assertEqual(math_schema.state(db), 'partial')
        self.assertEqual(len(upgrade(self.path)), 6)

    def test_a_different_existing_definition_stops_everything(self):
        with closing(sqlite3.connect(self.path)) as db:
            db.execute('ALTER TABLE math_concepts ADD COLUMN retired_at INTEGER')
            db.commit()
        before = self.path.read_bytes()
        with self.assertRaisesRegex(ValueError, 'retired_at exists with a different definition'):
            upgrade(self.path)
        self.assertEqual(self.path.read_bytes(), before)

    def test_slugs_differing_only_in_case_or_spaces_stop_the_upgrade(self):
        for slug in ('Group', ' group '):
            with self.subTest(slug=slug):
                path = self.root / (slug.strip() + str(len(slug)) + '.db')
                shutil.copyfile(self.path, path)
                with closing(sqlite3.connect(path)) as db:
                    db.execute("INSERT INTO math_concepts(canonical_name, slug, title) VALUES ('Other', ?, 'other')",
                               (slug,))
                    db.commit()
                with self.assertRaisesRegex(ValueError, "slug 'group' is shared by Group, Other"):
                    upgrade(path)
                with closing(sqlite3.connect(path)) as db:
                    self.assertEqual(math_schema.state(db), 'invalid')

    def test_unique_slug_index_reserves_urls_ignoring_case(self):
        upgrade(self.path)
        with closing(sqlite3.connect(self.path)) as db, self.assertRaises(sqlite3.IntegrityError):
            db.execute("INSERT INTO math_concepts(canonical_name, slug, title) VALUES ('X', 'GROUP', 'x')")

    def test_schema_package_previews_checks_and_publishes_once(self):
        data = zipped('math-schema.json', math_schema.payload())
        self.assertIn('ALTER TABLE math_concepts ADD COLUMN retired_at TEXT', preview(data))
        self.assertIn('ELIGIBLE', preview(data, self.path, live=True).splitlines()[-3])
        backups = self.root / 'backups'
        result = publish(data, self.path, backups, SOURCE)
        self.assertEqual(result['status'], 'APPLIED')
        self.assertTrue(Path(result['backup']).is_file())
        self.assertEqual(publish(data, self.path, backups, SOURCE)['status'], 'ALREADY_PRESENT')
        self.assertTrue(preview(data, self.path, live=True).splitlines()[-3].startswith('ALREADY PRESENT'))
        with self.assertRaisesRegex(ValueError, 'Invalid schema upgrade package'):
            publish(zipped('math-schema.json', dict(math_schema.payload(), extra='DROP TABLE x')),
                    self.path, backups, SOURCE)


class ExistingPackageTests(TempFolder):
    """Packages prepared before the upgrade still validate and apply after it."""

    def setUp(self):
        super().setUp()
        self.path = self.root / 'math.db'
        self.ids = make_catalog(self.path, upgraded=False)
        self.backups = self.root / 'backups'

    def test_snapshot_is_identical_before_and_after_the_upgrade(self):
        before = read_snapshot(self.path)
        upgrade(self.path)
        self.assertEqual(read_snapshot(self.path), before)
        self.assertEqual({name: item['retired'] for name, item in read_status(self.path).items()},
                         dict.fromkeys(before, False))

    def text_patch(self, canonical='Group', tex='A group is a set with one operation.'):
        expected = read_snapshot(self.path)[canonical]
        return zipped('patch.json', dict(canonical_name=canonical, expected=expected, replacement_tex=tex))

    def new_entry(self, **changes):
        entry = dict(canonical_name='Coset', slug='coset', title='coset', owner='CWoo', cleaned_tex='A coset.',
                     is_cleaned=1, classifications=['20A05'], types=['Definition'], synonyms=[], definitions=[],
                     link_exclusions=[], related_concepts=['Group'])
        entry.update(changes)
        return zipped('entry.json', entry)

    def test_old_text_patch_and_new_entry_apply_on_an_upgraded_database(self):
        patch, entry = self.text_patch(), self.new_entry()
        upgrade(self.path)
        self.assertEqual(publish(patch, self.path, self.backups, SOURCE)['status'], 'APPLIED')
        self.assertEqual(publish(entry, self.path, self.backups, SOURCE)['status'], 'APPLIED')

    def test_text_patch_to_a_retired_entry_is_refused(self):
        patch = self.text_patch('OldStub', 'Finished.')
        upgrade(self.path)
        retire_by_hand(self.path, self.ids['old stub'])
        self.assertIn('retired', preview(patch, self.path, live=True).splitlines()[-3])
        before = self.path.read_bytes()
        with self.assertRaisesRegex(ValueError, 'retired'):
            publish(patch, self.path, self.backups, SOURCE)
        self.assertEqual(self.path.read_bytes(), before)

    def test_new_entry_relating_to_a_merged_entry_is_told_the_survivor(self):
        upgrade(self.path)
        merge_by_hand(self.path, self.ids['monoid with inverses'], self.ids['group'])
        entry = self.new_entry(related_concepts=['MonoidWithInverses'])
        self.assertIn('relate to Group instead', preview(entry, self.path, live=True))
        with self.assertRaisesRegex(ValueError, 'relate to Group instead'):
            publish(entry, self.path, self.backups, SOURCE)

    def test_new_entry_may_reuse_a_plainly_retired_title_but_not_its_slug(self):
        upgrade(self.path)
        retire_by_hand(self.path, self.ids['old stub'])
        self.assertEqual(publish(self.new_entry(canonical_name='OldStubRevisited', slug='old-stub-revisited',
                                                title='old stub', related_concepts=[]),
                                 self.path, self.backups, SOURCE)['status'], 'APPLIED')
        with self.assertRaisesRegex(ValueError, 'Duplicate slug'):
            publish(self.new_entry(canonical_name='OldStub2', slug='old-stub', title='stub two', related_concepts=[]),
                    self.path, self.backups, SOURCE)


class OptionEightUpgradeTests(TempFolder):
    def setUp(self):
        super().setUp()
        self.base, self.local, self.live = (self.root / name for name in ('base.db', 'working.db', 'live.db'))
        make_catalog(self.base, upgraded=False)
        shutil.copyfile(self.base, self.local)
        shutil.copyfile(self.base, self.live)
        upgrade(self.live)
        self.state = dict(base=str(self.base), working=str(self.local), base_sha256=self.digest(self.base),
                          username='cwoo', job=None)

    def digest(self, path):
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()

    def run_refresh(self):
        self.live.with_name('snapshot.json').write_text(json.dumps(dict(
            sha256=self.digest(self.live), source='/home/cwoo/chi-portfolio/backend/portfolio.db')))
        (self.root / 'diagrams').mkdir(exist_ok=True)
        from unittest.mock import patch
        with patch('bring_changes_home.diagram_home.stage_media', return_value=({}, {}, dict(
                verified=[], kept_local=[], missing_on_server=[]))), \
                patch('bring_changes_home.diagram_home.install_media'):
            return refresh(self.state, self.live, self.root / 'copies', Mock(), diagrams=self.root / 'diagrams')

    def test_known_upgrade_on_live_alone_is_brought_home(self):
        originals = self.digest(self.base), self.digest(self.local)
        result = self.run_refresh()
        self.assertTrue(result['safe'], result)
        self.assertEqual((self.digest(self.base), self.digest(self.local)), originals)
        self.assertEqual(self.digest(self.state['working']), self.digest(self.live))
        self.assertEqual(sorted(p.name for p in Path(result['report']).parent.iterdir()),
                         ['base.db', 'comparison.json', 'previous-workflow.json', 'working.db'])

    def test_unpublished_local_edit_still_blocks_across_the_upgrade(self):
        with closing(sqlite3.connect(self.local)) as db:
            db.execute("UPDATE math_concepts SET cleaned_tex = 'Unpublished.' WHERE slug = 'group'")
            db.commit()
        result = self.run_refresh()
        self.assertFalse(result['safe'])
        self.assertIn('math_concepts', result['blocked'])

    def test_any_other_schema_difference_still_stops(self):
        with closing(sqlite3.connect(self.live)) as db:
            db.execute('CREATE TABLE something_else (x)')
            db.commit()
        result = self.run_refresh()
        self.assertFalse(result['safe'])
        self.assertIn('schemas differ', result['reason'])


class CodeContractGuardTests(TempFolder):
    def setUp(self):
        super().setUp()
        self.site = self.root / 'site'
        self.database = self.site / 'backend' / 'portfolio.db'
        self.database.parent.mkdir(parents=True)
        self.ids = make_catalog(self.database)
        self.contract = self.site / frontend_sync.CONTRACT_FILE
        self.contract.parent.mkdir(parents=True)
        self.contract.write_text('RETIREMENT_CONTRACT = 1\n')
        self.reader = self.site / 'backend/src/services/math/reader.py'
        self.reader.write_text('VERSION = 1\n')

    def payload(self, files):
        return dict(kind='website-code', files=[
            dict(path=path, expected=(self.site / path).read_text() if (self.site / path).exists() else None,
                 replacement=text) for path, text in files.items()])

    def verdict(self, files):
        return frontend_sync.status(self.payload(files), self.site, self.database)

    def test_no_requirement_before_any_retirement(self):
        self.contract.unlink()
        self.assertTrue(self.verdict({'backend/src/services/math/reader.py': 'VERSION = 2\n'}).startswith('EXPECTED'))

    def test_live_retirements_need_code_declaring_their_contract(self):
        retire_by_hand(self.database, self.ids['old stub'])
        reader = 'backend/src/services/math/reader.py'
        self.assertTrue(self.verdict({reader: 'VERSION = 2\n'}).startswith('EXPECTED'))
        self.assertTrue(self.verdict({reader: 'VERSION = 2\n', frontend_sync.CONTRACT_FILE:
                                      'RETIREMENT_CONTRACT = 1  # same\n'}).startswith('EXPECTED'))
        for text in ('RETIREMENT_CONTRACT = 0\n', 'RETIREMENT_CONTRACT = int("1")\n', 'OTHER = 1\n'):
            with self.subTest(text=text):
                verdict = self.verdict({reader: 'VERSION = 2\n', frontend_sync.CONTRACT_FILE: text})
                self.assertTrue(verdict.startswith('BLOCKED'), verdict)
        self.contract.unlink()
        self.assertTrue(self.verdict({reader: 'VERSION = 2\n'}).startswith('BLOCKED'))

    def test_publish_refuses_before_writing_anything(self):
        retire_by_hand(self.database, self.ids['old stub'])
        payload = self.payload({frontend_sync.CONTRACT_FILE: 'RETIREMENT_CONTRACT = 0\n'})
        data = zipped('website-code.json', payload)
        with self.assertRaisesRegex(ValueError, 'retirement contract 1'):
            publish(data, self.database, self.root / 'backups', self.database.parent / 'src')
        self.assertEqual(self.contract.read_text(), 'RETIREMENT_CONTRACT = 1\n')

    def test_this_checkout_declares_a_contract_the_guard_can_read(self):
        text = (SOURCE / 'services/math/retirement.py').read_text(encoding='utf-8')
        self.assertEqual(frontend_sync.declared_contract(text), 1)


if __name__ == '__main__':
    unittest.main()
