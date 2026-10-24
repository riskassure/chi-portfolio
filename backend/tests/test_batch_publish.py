"""Option 20: plan, check and publish a batch of new math entries without changing authored content."""
from contextlib import closing
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import batch_check
from batch_links import cycles, dependants, entry_links, name_index, publish_order, resolve
import batch_publish as bp
from services.math.render_helper import render_prose_latex_to_html
from test_diagram_publish import link_or_copy
from test_diagram_sync import TREE, create_db, svg_for
import diagram_sync
import website_workflow as w

SOURCE = Path(__file__).resolve().parents[1] / 'src'


def add_entry(path, canonical, tex='Text.', related=(), title=None, slug=None, synonyms=()):
    title = title or canonical
    slug = slug or '-'.join(part.lower() for part in __import__('re').findall('[A-Z][a-z]*', canonical))
    with closing(sqlite3.connect(path)) as db:
        ident = db.execute('INSERT INTO math_concepts(canonical_name,slug,title,owner,cleaned_tex,is_cleaned,rendered_tex,'
                           "created_at,updated_at) VALUES(?,?,?,'CWoo',?,1,'','t','t')", (canonical, slug, title, tex)).lastrowid
        db.execute('INSERT INTO math_concept_classifications VALUES(?,1)', (ident,))
        db.execute('INSERT INTO math_concept_types VALUES(?,1)', (ident,))
        for synonym in synonyms:
            db.execute('INSERT INTO math_synonyms VALUES(?,?)', (ident, synonym))
        for target in related:
            row = db.execute('SELECT id FROM math_concepts WHERE canonical_name=?', (target,)).fetchone()
            db.execute('INSERT INTO math_related_concepts VALUES(?,?,?)', (ident, target, row[0] if row else None))
        db.commit()


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class LinkAndOrderTests(unittest.TestCase):
    def test_order_follows_dependencies_and_keeps_selection_order_otherwise(self):
        graph = {'C': {'A'}, 'A': set(), 'B': set(), 'D': {'C', 'B'}}
        self.assertEqual(publish_order(graph, ['D', 'C', 'B', 'A']), ['B', 'A', 'C', 'D'])

    def test_loops_are_found_with_everything_that_needs_them(self):
        graph = {'A': {'B'}, 'B': {'A'}, 'C': {'C'}, 'D': {'A'}, 'E': {'D'}, 'F': set()}
        self.assertEqual(cycles(graph), [['A', 'B'], ['C']])
        self.assertEqual(dependants(graph, ['A', 'B']), ['D', 'E'])
        with self.assertRaises(ValueError):
            publish_order(graph, list(graph))

    def test_explicit_links_resolve_like_the_site(self):
        index = name_index(['Group', 'Ring', 'RING', 'Field'])
        self.assertEqual(resolve(' group '.strip(), index), ('resolved', 'Group'))
        self.assertEqual(resolve('ring', index), ('ambiguous', None))
        self.assertEqual(resolve('group-theory', index), ('unresolved', None))
        tex = r'See \PMlinkname{groups}{Group}, \PMlinkname{a \emph{field}}{ field } and \PMlinkname{me}{Monoid}.'
        links = entry_links('Monoid', tex, render_prose_latex_to_html, name_index(['Group', 'Field', 'Monoid']))
        self.assertEqual([(l['text'], l['target'], l['status'], l['canonical'], l['self_link']) for l in links],
                         [('groups', 'Group', 'resolved', 'Group', False),
                          ('a field', 'field', 'resolved', 'Field', False),
                          ('me', 'Monoid', 'resolved', 'Monoid', True)])


class BatchFixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.base, self.working = self.root / 'base.db', self.root / 'working.db'
        create_db(self.base, None)
        add_entry(self.base, 'Group', 'A group is a set.')
        shutil.copyfile(self.base, self.working)
        self.state = dict(base=str(self.base), base_sha256=w.digest(self.base), working=str(self.working),
                          username='cwoo', job=None)
        (self.root / 'diagrams').mkdir()
        self.patches = [patch.object(w, 'save'), patch.object(bp, 'BATCHES', self.root / 'batches'),
                        patch.object(w, 'DIAGRAMS', self.root / 'diagrams'), patch.object(bp.time, 'sleep')]
        for item in self.patches:
            item.start()

    def tearDown(self):
        for item in reversed(self.patches):
            item.stop()
        self.temp.cleanup()

    def plan(self, selected, title, live=None):
        """Plan with the live site's names; by default the live site matches the baseline."""
        return bp.plan(self.state, selected, title, sorted(bp.read_snapshot(self.base)) if live is None else live)

    def add_batch(self):
        """Three new entries: Subgroup needs Group (live); Coset needs Subgroup; Index links to Coset."""
        add_entry(self.working, 'Subgroup', r'A subset of a \PMlinkname{group}{Group}.', related=['Group'])
        add_entry(self.working, 'Coset', 'A translate of a subgroup.', related=['Subgroup'])
        add_entry(self.working, 'IndexOfASubgroup', r'The number of \PMlinkname{cosets}{Coset}.')


class PlanTests(BatchFixture):
    def test_plan_orders_freezes_and_changes_no_database(self):
        self.add_batch()
        before = file_hash(self.base), file_hash(self.working)
        manifest, lines = self.plan(['IndexOfASubgroup', 'Coset', 'Subgroup'], 'groups')
        self.assertEqual(manifest['order'], ['Subgroup', 'Coset', 'IndexOfASubgroup'])
        self.assertEqual((file_hash(self.base), file_hash(self.working)), before)
        self.assertEqual(manifest['entries']['IndexOfASubgroup']['needs'], ['Coset'])
        self.assertEqual(manifest['entries']['Subgroup']['needs'], [])
        for name in manifest['order']:
            entry = manifest['entries'][name]
            self.assertEqual(file_hash(entry['package']), entry['sha256'])
            self.assertEqual(entry['state'], 'pending')
        review = Path(manifest['review_file']).read_text(encoding='utf-8')
        self.assertIn('explicit link "cosets" → Coset resolves to Coset', review)
        self.assertIn('"cleaned_tex": "A translate of a subgroup."', review)
        self.assertEqual(json.loads((Path(manifest['folder']) / 'manifest.json').read_text())['order'], manifest['order'])
        self.assertIn('Subgroup', '\n'.join(lines))

    def test_loop_blocks_the_batch_and_keeps_both_links(self):
        add_entry(self.working, 'LeftCoset', 'Text.', related=['RightCoset'])
        add_entry(self.working, 'RightCoset', 'Text.', related=['LeftCoset'])
        add_entry(self.working, 'Coset', 'Text.', related=['LeftCoset'])
        add_entry(self.working, 'Monoid', 'Text.')
        before = file_hash(self.working)
        manifest, lines = self.plan(['LeftCoset', 'RightCoset', 'Coset', 'Monoid'], 'cosets')
        self.assertIsNone(manifest)
        report = '\n'.join(lines)
        self.assertIn('LeftCoset ↔ RightCoset', report)
        self.assertIn('remove LeftCoset, RightCoset, Coset from the selection', report)
        self.assertNotIn('Monoid from', report)
        self.assertEqual(file_hash(self.working), before)
        self.assertFalse((self.root / 'batches').exists())
        manifest, _ = self.plan(['Monoid'], 'monoid')
        self.assertEqual(manifest['order'], ['Monoid'])

    def test_unresolved_ambiguous_and_outside_targets_block(self):
        add_entry(self.base, 'RING', 'Old.', slug='ring-upper')
        add_entry(self.base, 'Ring', 'Old.', slug='ring')
        shutil.copyfile(self.base, self.working)
        self.state['base_sha256'] = w.digest(self.base)
        add_entry(self.working, 'Draft', 'Not selected.')
        add_entry(self.working, 'Ideal', r'In a \PMlinkname{ring}{ring}, see \PMlinkname{x}{NoSuchEntry} '
                                         r'and \PMlinkname{d}{Draft}.', related=['Draft'])
        manifest, lines = self.plan(['Ideal'], 'ideal')
        report = '\n'.join(lines)
        self.assertIsNone(manifest)
        self.assertIn('ring matches more than one canonical name', report)
        self.assertIn('NoSuchEntry matches no live entry or entry in this batch', report)
        self.assertIn('Draft matches no live entry or entry in this batch (a local entry not in this batch)', report)
        self.assertIn('Ideal is related to Draft, which is not on the live site and not in this batch', report)

    def test_dependencies_are_checked_against_the_live_site_not_an_older_baseline(self):
        # Ring went live after the baseline was taken; Field was removed from the live site since.
        add_entry(self.base, 'Field', 'Old.')
        shutil.copyfile(self.base, self.working)
        self.state['base_sha256'] = w.digest(self.base)
        add_entry(self.working, 'Ring', 'Live since the baseline.')
        add_entry(self.working, 'Ideal', r'A subset of a \PMlinkname{ring}{Ring}.', related=['Ring'])
        add_entry(self.working, 'Subfield', 'Text.', related=['Field'])
        live = ['Group', 'Ring']
        manifest, lines = self.plan(['Ideal'], 'ideals', live)
        self.assertIsNotNone(manifest, lines)
        self.assertEqual(manifest['entries']['Ideal']['needs'], [])
        self.assertEqual(manifest['entries']['Ideal']['links'][0]['canonical'], 'Ring')
        manifest, lines = self.plan(['Subfield'], 'fields', live)
        self.assertIsNone(manifest)
        self.assertIn('Subfield is related to Field, which is not on the live site and not in this batch', '\n'.join(lines))

    def test_names_clashing_inside_the_batch_block(self):
        add_entry(self.working, 'NormalSubgroup', 'Text.', synonyms=['Invariant subgroup'])
        add_entry(self.working, 'InvariantSubgroup', 'Text.', title='Invariant subgroup', slug='invariant-subgroup')
        manifest, lines = self.plan(['NormalSubgroup', 'InvariantSubgroup'], 'normal')
        self.assertIsNone(manifest)
        self.assertIn("InvariantSubgroup's title is a synonym or defined term of NormalSubgroup", '\n'.join(lines))

    def test_selection_parsing(self):
        self.assertEqual(bp.parse_selection('3, 1-2,2', 4), [2, 0, 1])
        self.assertEqual(bp.parse_selection('all', 3), [0, 1, 2])
        for bad in ('0', '5', '2-1', 'x'):
            with self.assertRaises(ValueError):
                bp.parse_selection(bad, 4)


class ShippedModuleTests(unittest.TestCase):
    def test_batch_check_ships_everything_the_single_entry_check_ships(self):
        import preflight_live_package
        self.assertLessEqual(set(preflight_live_package.MODULES), set(batch_check.MODULES))


class RemoteCheckTests(BatchFixture):
    """The batch check runs in an isolated interpreter with only its shipped modules, as over SSH."""

    def setUp(self):
        super().setUp()
        backend = self.root / 'home' / 'chi-portfolio' / 'backend'
        (backend / 'data' / 'math' / 'diagrams').mkdir(parents=True)
        link_or_copy(SOURCE, backend / 'src')
        self.live = backend / 'portfolio.db'
        shutil.copyfile(self.base, self.live)

    def run_check(self, manifest, names, projected):
        request = batch_check.build_request('cwoo', [dict(package=manifest['entries'][n]['package']) for n in names], projected)
        request['database'] = str(self.live)
        before = file_hash(self.live)
        result = subprocess.run([sys.executable, '-I', '-B', '-c', batch_check.BOOTSTRAP], input=json.dumps(request),
                                capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(file_hash(self.live), before)
        report = self.root / ('report-' + str(len(list(self.root.glob('report-*')))) + '.txt')
        response = batch_check.read_response(result.stdout, request, report)
        return {r['canonical']: (r['status'], batch_check.problems(r, projected)) for r in response['results']}

    def test_projected_batch_passes_but_each_entry_needs_its_dependencies_live(self):
        self.add_batch()
        manifest, _ = self.plan(['Subgroup', 'Coset', 'IndexOfASubgroup'], 'groups')
        projected = self.run_check(manifest, manifest['order'], True)
        self.assertTrue(all(status.startswith('NO DUPLICATE FOUND') and not found
                            for status, found in projected.values()), projected)
        strict = self.run_check(manifest, ['Coset', 'IndexOfASubgroup'], False)
        self.assertIn('Missing live related_concepts: Subgroup', strict['Coset'][0])
        self.assertIn('IndexOfASubgroup', strict)
        self.assertEqual(strict['IndexOfASubgroup'][1], ['explicit link "cosets" → Coset matches no live entry'])
        self.assertEqual(self.run_check(manifest, ['Subgroup'], False)['Subgroup'], (
            'NO DUPLICATE FOUND — eligible for further review', []))

    def test_live_catalog_is_read_in_isolation_and_plans_against_the_live_site(self):
        add_entry(self.live, 'Ring', 'Created live after the baseline.')
        add_entry(self.working, 'Ideal', r'A subset of a \PMlinkname{ring}{Ring}.', related=['Ring'])
        request = batch_check.catalog_request('cwoo')
        request['database'] = str(self.live)
        before = file_hash(self.live)
        result = subprocess.run([sys.executable, '-I', '-B', '-c', batch_check.CATALOG_BOOTSTRAP], input=json.dumps(request),
                                capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(file_hash(self.live), before)
        live = batch_check.read_catalog(result.stdout)
        self.assertEqual(live, ['Group', 'Ring'])
        manifest, lines = self.plan(['Ideal'], 'ideals', live)
        self.assertIsNotNone(manifest, lines)
        self.assertEqual(self.run_check(manifest, ['Ideal'], False)['Ideal'], ('NO DUPLICATE FOUND — eligible for further review', []))

    def test_already_present_needs_a_full_match(self):
        self.add_batch()
        manifest, _ = self.plan(['Subgroup'], 'one')
        add_entry(self.live, 'Subgroup', r'A subset of a \PMlinkname{group}{Group}.', related=['Group'])
        self.assertTrue(self.run_check(manifest, ['Subgroup'], False)['Subgroup'][0].startswith('ALREADY PRESENT'))
        with closing(sqlite3.connect(self.live)) as db:
            db.execute("INSERT INTO math_synonyms SELECT id, 'Sub-group' FROM math_concepts WHERE canonical_name='Subgroup'")
            db.commit()
        status, found = self.run_check(manifest, ['Subgroup'], False)['Subgroup']
        self.assertTrue(status.startswith('BLOCKED — Duplicate canonical_name'), status)
        self.assertEqual(found, [status])

    def test_new_entry_with_diagrams_needs_its_rows_and_files_for_already_present(self):
        add_entry(self.working, 'RootedTree', 'A rooted tree:\n' + TREE)
        diagram_sync.render_missing(self.working, 'RootedTree', self.root / 'diagrams', svg_for)
        manifest, _ = self.plan(['RootedTree'], 'trees')
        entry = manifest['entries']['RootedTree']
        self.assertTrue(entry['diagrams'])
        preview = Path(manifest['folder']) / 'previews' / entry['diagram_files'][0]['file']
        self.assertEqual(hashlib.sha256(preview.read_bytes()).hexdigest(), entry['diagram_files'][0]['sha256'])
        self.assertTrue(self.run_check(manifest, ['RootedTree'], True)['RootedTree'][0].startswith('NO DUPLICATE FOUND'))
        # The live site gets the same entry and rows, but the SVG file is missing: not a full match.
        with closing(sqlite3.connect(self.working)) as source, closing(sqlite3.connect(self.live)) as live:
            add_entry(self.live, 'RootedTree', 'A rooted tree:\n' + TREE, slug='rooted-tree')
            ident = live.execute("SELECT id FROM math_concepts WHERE canonical_name='RootedTree'").fetchone()[0]
            for row in source.execute('SELECT block_index, source_hash, source_tex, svg_path, created_at FROM math_concept_diagrams'):
                live.execute('INSERT INTO math_concept_diagrams(concept_id,block_index,source_hash,source_tex,svg_path,created_at) '
                             'VALUES(?,?,?,?,?,?)', (ident,) + row)
            live.commit()
        status, found = self.run_check(manifest, ['RootedTree'], False)['RootedTree']
        self.assertTrue(status.startswith('CONFLICT'), status)
        shutil.copyfile(preview, self.live.parent / 'data' / 'math' / 'diagrams' / preview.name.rsplit('-', 1)[-1])
        self.assertTrue(self.run_check(manifest, ['RootedTree'], False)['RootedTree'][0].startswith('ALREADY PRESENT'))

    def test_a_blocked_entry_blocks_what_needs_it_in_the_projection(self):
        self.add_batch()
        manifest, _ = self.plan(['Subgroup', 'Coset'], 'two')
        add_entry(self.live, 'Subgroup2', 'Clash.', title='Subgroup', slug='subgroup-2')
        projected = self.run_check(manifest, manifest['order'], True)
        self.assertIn('Duplicate title', projected['Subgroup'][0])
        self.assertIn('Missing live related_concepts: Subgroup', projected['Coset'][0])


class FakeSite:
    """Stand-in for staging, the live check and publishing: entries need their dependencies live."""

    def __init__(self, manifest_needs):
        self.needs, self.live, self.published, self.failures, self.after_failure = manifest_needs, set(), [], {}, {}

    def stage(self, settings, package):
        return '/home/cwoo/chi-portfolio-staging/' + 'a' * 32 + '/package.zip', file_hash(package)

    def check(self, manifest, names, projected, remote=False):
        result = {}
        for name in names:
            if name in self.live:
                status = 'ALREADY PRESENT — do not apply again'
            elif name in self.after_failure and not projected:
                status = self.after_failure.pop(name)
            elif projected or self.needs[name] <= self.live:
                status = 'NO DUPLICATE FOUND — eligible for further review'
            else:
                status = 'BLOCKED — Missing live related_concepts: ' + ', '.join(sorted(self.needs[name] - self.live))
            entry = dict(canonical=name, status=status, links=[])
            result[name] = (entry, batch_check.problems(entry, projected))
        return result

    def publish(self, username, remote, package, receipt):
        name = next(n for n in self.needs if Path(package).parent.name.split('-', 1)[1] == self.slugs[n])
        self.published.append(name)
        failure = self.failures.get(name, [])
        if failure:
            went_through = failure.pop(0)
            if went_through:
                self.live.add(name)
            raise RuntimeError('Publication result is unconfirmed.')
        self.live.add(name)
        receipt.write_text('{}')
        return dict(status='APPLIED', canonical=name, backup='b.db')


class PublishTests(BatchFixture):
    def setUp(self):
        super().setUp()
        self.add_batch()
        settings = self.root / 'settings.json'
        settings.write_text('{}')
        self.patches += [patch.object(bp, 'SETTINGS', settings),
                         patch.object(bp, 'validate', lambda s: dict(username='cwoo'))]
        for item in self.patches[-2:]:
            item.start()

    def make(self, names=('Subgroup', 'Coset', 'IndexOfASubgroup')):
        manifest, _ = self.plan(list(names), 'groups')
        self.state['batch'] = manifest['folder']
        site = FakeSite({n: set(manifest['entries'][n]['needs']) | ({'Group'} if n == 'Subgroup' else set())
                         for n in manifest['order']})
        site.live.add('Group')
        site.slugs = {n: manifest['entries'][n]['slug'] for n in manifest['order']}
        return manifest, site

    def run_option(self, site, answers, bring_home=None):
        bring_home = bring_home or (lambda state: dict(safe=True, report='r.json'))
        with patch.object(bp, 'stage', site.stage), patch.object(bp, 'check', site.check), \
                patch.object(bp, 'publish_staged', site.publish), patch.object(w, 'bring_home', bring_home), \
                patch.object(batch_check, 'live_catalog', lambda username: sorted(site.live)), \
                patch('builtins.input', side_effect=list(answers)):
            bp.run(self.state)

    def manifest(self, manifest):
        return json.loads((Path(manifest['folder']) / 'manifest.json').read_text())

    def test_publish_all_in_order_then_verify_and_bring_home(self):
        manifest, site = self.make()
        before = file_hash(self.working)
        self.run_option(site, ['RESUME', 'PUBLISH ALL', 'VERIFIED'])
        self.assertEqual(site.published, ['Subgroup', 'Coset', 'IndexOfASubgroup'])
        saved = self.manifest(manifest)
        self.assertEqual([saved['entries'][n]['state'] for n in saved['order']], ['applied'] * 3)
        self.assertEqual((saved['publication'], saved['verification']['status'], saved['synchronization']['status']),
                         ('complete', 'verified', 'complete'))
        self.assertNotIn('batch', self.state)
        self.assertEqual(file_hash(self.working), before)
        self.assertEqual(bp.time.sleep.call_count, 2)

    def test_cancelling_publishes_nothing_and_keeps_the_batch(self):
        manifest, site = self.make()
        self.run_option(site, ['RESUME', 'no'])
        self.assertEqual(site.published, [])
        self.assertEqual(self.manifest(manifest)['publication'], 'planned')
        self.assertEqual(self.state['batch'], manifest['folder'])

    def test_a_blocked_entry_stops_the_batch_and_resume_continues(self):
        manifest, site = self.make()
        site.after_failure['Coset'] = 'CONFLICT — someone added it differently'
        with self.assertRaisesRegex(bp.BatchStopped, 'Coset cannot be published now'):
            self.run_option(site, ['RESUME', 'PUBLISH ALL'])
        saved = self.manifest(manifest)
        self.assertEqual(site.published, ['Subgroup'])
        self.assertEqual([saved['entries'][n]['state'] for n in saved['order']], ['applied', 'blocked', 'pending'])
        self.assertEqual(saved['publication'], 'stopped')
        self.run_option(site, ['RESUME', 'VERIFIED'])
        self.assertEqual(site.published, ['Subgroup', 'Coset', 'IndexOfASubgroup'])

    def test_an_entry_never_publishes_before_its_dependency(self):
        manifest, site = self.make()
        site.after_failure['Subgroup'] = 'CONFLICT — unexpected'
        with self.assertRaises(bp.BatchStopped):
            self.run_option(site, ['RESUME', 'PUBLISH ALL'])
        saved = self.manifest(manifest)
        self.assertEqual(site.published, [])
        self.assertEqual(saved['entries']['Subgroup']['state'], 'blocked')
        self.assertEqual(saved['entries']['Coset']['state'], 'pending')
        with self.assertRaisesRegex(bp.BatchStopped, 'needs Subgroup, which did not publish'):
            bp.publish_one(saved, 'Coset', {})

    def test_unconfirmed_publish_that_went_through_is_not_repeated(self):
        manifest, site = self.make(['Subgroup'])
        site.failures['Subgroup'] = [True]
        self.run_option(site, ['RESUME', 'PUBLISH ALL', 'VERIFIED'])
        saved = self.manifest(manifest)
        self.assertEqual(site.published, ['Subgroup'])
        self.assertEqual(saved['entries']['Subgroup']['state'], 'already_present')
        self.assertIn('confirmed by live check', [h['outcome'] for h in saved['entries']['Subgroup']['history']])

    def test_unconfirmed_publish_with_expected_earlier_state_is_retried(self):
        manifest, site = self.make(['Subgroup'])
        site.failures['Subgroup'] = [False]
        self.run_option(site, ['RESUME', 'PUBLISH ALL', 'VERIFIED'])
        self.assertEqual(site.published, ['Subgroup', 'Subgroup'])
        self.assertEqual(self.manifest(manifest)['entries']['Subgroup']['state'], 'applied')

    def test_still_unconfirmed_after_retries_stops_and_resume_reconciles(self):
        manifest, site = self.make(['Subgroup'])
        site.failures['Subgroup'] = [False, False, False, True]
        with self.assertRaisesRegex(bp.BatchStopped, 'still unconfirmed'):
            self.run_option(site, ['RESUME', 'PUBLISH ALL'])
        self.assertEqual(self.manifest(manifest)['entries']['Subgroup']['state'], 'publishing')
        self.run_option(site, ['RESUME', 'VERIFIED'])
        saved = self.manifest(manifest)
        self.assertEqual(len(site.published), 4)
        self.assertEqual(saved['entries']['Subgroup']['state'], 'already_present')

    def test_changed_frozen_package_invalidates_the_approval(self):
        manifest, site = self.make()
        site.after_failure['Coset'] = 'CONFLICT — stop here'
        with self.assertRaises(bp.BatchStopped):
            self.run_option(site, ['RESUME', 'PUBLISH ALL'])
        Path(manifest['entries']['IndexOfASubgroup']['package']).write_bytes(b'changed')
        with self.assertRaisesRegex(bp.BatchStopped, 'approval no longer holds'):
            self.run_option(site, ['RESUME'])
        self.assertEqual(self.manifest(manifest)['publication'], 'invalidated')
        self.assertEqual(site.published, ['Subgroup'])

    def test_later_working_copy_edits_never_enter_the_packages(self):
        manifest, site = self.make(['Subgroup'])
        frozen = Path(manifest['entries']['Subgroup']['package']).read_bytes()
        with closing(sqlite3.connect(self.working)) as db:
            db.execute("UPDATE math_concepts SET cleaned_tex='Edited later.' WHERE canonical_name='Subgroup'")
            db.commit()
        with self.assertRaisesRegex(bp.BatchStopped, 'Stopped before publishing'):
            self.run_option(site, ['RESUME', 'no'])
        self.assertEqual(site.published, [])
        self.run_option(site, ['RESUME', 'PUBLISH REVIEWED', 'PUBLISH ALL', 'VERIFIED'])
        self.assertEqual(site.published, ['Subgroup'])
        self.assertEqual(Path(manifest['entries']['Subgroup']['package']).read_bytes(), frozen)

    def test_a_second_run_on_the_same_batch_is_refused(self):
        manifest, site = self.make()
        (Path(manifest['folder']) / '.lock').write_text('{}')
        with self.assertRaisesRegex(bp.BatchStopped, 'Another option 20 run'):
            self.run_option(site, ['RESUME'])
        self.assertEqual(site.published, [])

    def test_set_aside_waits_for_the_lock_and_changes_nothing_while_another_run_holds_it(self):
        manifest, site = self.make()
        before = (Path(manifest['folder']) / 'manifest.json').read_text()
        with bp.locked(manifest):
            with self.assertRaisesRegex(bp.BatchStopped, 'Another option 20 run'):
                self.run_option(site, [])  # no prompt is shown, so SET ASIDE can't even be typed
        self.assertEqual((Path(manifest['folder']) / 'manifest.json').read_text(), before)
        self.assertEqual(self.state['batch'], manifest['folder'])
        self.run_option(site, ['SET ASIDE', ''])
        self.assertNotIn('batch', self.state)
        self.assertIn('set_aside', self.manifest(manifest))

    def test_the_batch_is_reloaded_after_taking_the_lock(self):
        manifest, site = self.make()
        stale = json.loads(json.dumps(manifest))
        manifest['publication'] = 'invalidated'  # what another run saved before releasing the lock
        bp.save_manifest(manifest)
        with patch.object(bp, 'load_manifest', lambda state: stale):
            with self.assertRaisesRegex(bp.BatchStopped, 'approval no longer holds'):
                self.run_option(site, ['RESUME'])
        self.assertEqual(site.published, [])

    def test_blocked_synchronization_is_kept_and_retried_without_republishing(self):
        manifest, site = self.make(['Subgroup'])
        self.run_option(site, ['RESUME', 'PUBLISH ALL', 'VERIFIED'],
                        bring_home=lambda state: dict(safe=False, report='r.json'))
        saved = self.manifest(manifest)
        self.assertEqual((saved['publication'], saved['synchronization']['status']), ('complete', 'blocked'))
        self.assertEqual(self.state['batch'], manifest['folder'])
        self.run_option(site, ['RESUME'])
        self.assertEqual(site.published, ['Subgroup'])
        self.assertEqual(self.manifest(manifest)['synchronization']['status'], 'complete')

    def test_verification_is_recorded_not_assumed(self):
        manifest, site = self.make(['Subgroup'])
        self.run_option(site, ['RESUME', 'PUBLISH ALL', 'later'])
        saved = self.manifest(manifest)
        self.assertEqual(saved['publication'], 'complete')
        self.assertIsNone(saved['verification'])
        self.assertIsNone(saved['synchronization'])

    def test_set_aside_keeps_history_and_starts_a_new_selection(self):
        manifest, site = self.make(['Subgroup'])
        self.run_option(site, ['SET ASIDE', ''])
        self.assertNotIn('batch', self.state)
        self.assertIn('set_aside', self.manifest(manifest))


if __name__ == '__main__':
    unittest.main()
