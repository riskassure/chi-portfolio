"""Step 8: write a finished option 20 batch as a migration, replay it, and record it in git (option 23)."""
from contextlib import closing
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import batch_check
import batch_publish as bp
import batch_record
import diagram_sync
from live_math_publication import publish
from test_batch_publish import BatchFixture, FakeSite, add_entry
from test_diagram_sync import TREE, svg_for
import website_workflow as w

MIGRATIONS = Path(__file__).resolve().parents[1] / 'src' / 'database' / 'math' / 'migrations'
sys.path.insert(0, str(MIGRATIONS))
import math_entry_record as record  # noqa: E402

SOURCE = Path(__file__).resolve().parents[1] / 'src'


def rows(path, canonical):
    with closing(sqlite3.connect(path)) as db:
        return (bp.read_snapshot(path).get(canonical),
                db.execute('SELECT c.id FROM math_concepts c WHERE canonical_name=?', (canonical,)).fetchone(),
                sorted(db.execute('SELECT d.block_index, d.source_hash, d.source_tex, d.svg_path FROM math_concept_diagrams d '
                                  'JOIN math_concepts c ON c.id=d.concept_id WHERE c.canonical_name=?', (canonical,))))


class FinishedBatch(BatchFixture):
    """A batch published through option 20, with the live site played by the baseline database itself."""

    def setUp(self):
        super().setUp()
        settings = self.root / 'settings.json'
        settings.write_text('{}')
        self.patches += [patch.object(bp, 'SETTINGS', settings),
                         patch.object(bp, 'validate', lambda s: dict(username='cwoo'))]
        for item in self.patches[-2:]:
            item.start()
        add_entry(self.working, 'Subgroup', r'A subset of a \PMlinkname{group}{Group}.', related=['Group'])
        add_entry(self.working, 'Coset', "A translate of a subgroup, ''written'' with quotes.", related=['Subgroup'])
        add_entry(self.working, 'RootedTree', 'A rooted tree:\n' + TREE, slug='rooted-tree')
        diagram_sync.render_missing(self.working, 'RootedTree', self.root / 'diagrams', svg_for)
        (self.root / 'data' / 'math' / 'diagrams').mkdir(parents=True)  # The "live" site's diagram folder.
        self.before = self.root / 'before.db'
        shutil.copyfile(self.base, self.before)
        self.manifest = self.finish(['Coset', 'RootedTree', 'Subgroup'])

    def finish(self, names):
        """Plan, publish (into the baseline, as live would), verify and bring home."""
        manifest, _ = self.plan(names, 'group basics')
        self.state['batch'] = manifest['folder']
        site = FakeSite({n: set() for n in manifest['order']})
        site.slugs = {n: manifest['entries'][n]['slug'] for n in manifest['order']}
        real = site.publish

        def publish_into_base(username, remote, package, receipt):
            publish(Path(package).read_bytes(), self.base, self.root / 'live-backups', SOURCE)
            return real(username, remote, package, receipt)
        site.publish = publish_into_base
        with patch.object(bp, 'stage', site.stage), patch.object(bp, 'check', site.check), \
                patch.object(bp, 'publish_staged', site.publish), \
                patch.object(w, 'bring_home', lambda state: dict(safe=True, report='r.json')), \
                patch.object(batch_check, 'live_catalog', lambda username: sorted(site.live | {'Group'})), \
                patch('builtins.input', side_effect=['RESUME', 'PUBLISH ALL', 'VERIFIED']):
            bp.run(self.state)
        return json.loads((Path(manifest['folder']) / 'manifest.json').read_text(encoding='utf-8'))


class MigrationTests(FinishedBatch):
    def test_records_follow_publish_order_with_the_reviewed_payloads(self):
        records, files = record.records_from_manifest(self.manifest)
        self.assertEqual([r['canonical_name'] for r in records], self.manifest['order'])
        self.assertLess(self.manifest['order'].index('Subgroup'), self.manifest['order'].index('Coset'))
        kinds = {r['canonical_name']: r['kind'] for r in records}
        self.assertEqual(kinds, dict(Subgroup='entry', Coset='entry', RootedTree='diagrams'))
        self.assertEqual(list(files), [diagram_sync.svg_name(records[[r['canonical_name'] for r in records].index('RootedTree')]
                                                              ['payload']['diagrams'][0]['source_hash'])])

    def test_written_migration_rebuilds_the_batch_with_live_ids(self):
        out = self.root / 'migrations' / 'add_group_basics_entries_20261030.py'
        out.parent.mkdir()
        written = record.write_migration(out, self.manifest)
        self.assertEqual(len(written), 2)  # The migration and one SVG.
        text = out.read_text(encoding='utf-8')
        self.assertIn('Entries of the option 20 batch "group basics"', text)
        self.assertIn('[diagrams]', text)
        self.assertEqual(record.load_entries(out), record.records_from_manifest(self.manifest)[0])
        env = dict(os.environ, PYTHONPATH=str(MIGRATIONS))
        target = self.root / 'replay' / 'catalog.db'
        target.parent.mkdir()
        shutil.copyfile(self.before, target)
        preview = subprocess.run([sys.executable, str(out), '--db', str(target)], capture_output=True, text=True,
                                 env=env, timeout=120)
        self.assertEqual(preview.returncode, 0, preview.stderr)
        self.assertIn('PREVIEW ONLY', preview.stdout)
        self.assertIn('New entries (3)', preview.stdout)
        self.assertEqual(bp.read_snapshot(target), bp.read_snapshot(self.before))
        applied = subprocess.run([sys.executable, str(out), '--db', str(target), '--apply'], capture_output=True,
                                 text=True, env=env, timeout=120)
        self.assertEqual(applied.returncode, 0, applied.stderr)
        self.assertTrue(list((target.parent / 'backups').glob('catalog.before-*.db')))
        for name in self.manifest['order']:
            self.assertEqual(rows(target, name), rows(self.base, name), name)
        svg = target.parent / 'data' / 'math' / 'diagrams'
        self.assertEqual(len(list(svg.glob('*.svg'))), 1)
        again = subprocess.run([sys.executable, str(out), '--db', str(target), '--apply'], capture_output=True,
                               text=True, env=env, timeout=120)
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertEqual(again.stdout.count('ALREADY_PRESENT'), 3)

    def test_write_never_overwrites(self):
        out = self.root / 'add_x_entries_20261030.py'
        out.write_text('mine')
        with self.assertRaises(FileExistsError):
            record.write_migration(out, self.manifest)
        self.assertEqual(out.read_text(), 'mine')

    def test_unfinished_batch_or_changed_package_is_refused(self):
        unfinished = json.loads(json.dumps(self.manifest))
        unfinished['entries']['Coset']['state'] = 'blocked'
        with self.assertRaisesRegex(ValueError, 'not live.*Coset'):
            record.records_from_manifest(unfinished)
        package = Path(self.manifest['entries']['Subgroup']['package'])
        package.write_bytes(package.read_bytes() + b' ')
        with self.assertRaisesRegex(ValueError, 'no longer matches'):
            record.records_from_manifest(self.manifest)

    def test_check_record_passes_and_catches_later_edits(self):
        out = self.root / 'm' / 'add_group_basics_entries_20261030.py'
        out.parent.mkdir()
        record.write_migration(out, self.manifest)
        assets = out.parent / record.ASSETS / out.stem
        before = w.digest(self.base)
        lines = record.check_record(record.load_entries(out), assets, self.base)
        self.assertIn('identical to the reference', lines[1])
        self.assertEqual(w.digest(self.base), before)  # Scratch copies only.
        with closing(sqlite3.connect(self.base)) as db:
            db.execute("UPDATE math_concepts SET cleaned_tex='Edited later.' WHERE canonical_name='Coset'")
            db.commit()
        with self.assertRaisesRegex(ValueError, 'differs from the reference database for: Coset'):
            record.check_record(record.load_entries(out), assets, self.base)

    def test_check_record_refuses_when_another_entry_points_at_the_batch(self):
        records, _ = record.records_from_manifest(self.manifest)
        add_entry(self.base, 'Normaliser', 'Later.', related=['Subgroup'])
        with self.assertRaisesRegex(ValueError, 'Normaliser points at an entry of the batch'):
            record.check_record(records, self.root, self.base)

    def test_a_tampered_svg_stops_the_replay(self):
        out = self.root / 'm' / 'add_group_basics_entries_20261030.py'
        out.parent.mkdir()
        record.write_migration(out, self.manifest)
        svg = next((out.parent / record.ASSETS / out.stem).glob('*.svg'))
        svg.write_bytes(svg.read_bytes().replace(b'57', b'58'))
        with self.assertRaisesRegex(ValueError, 'does not match its recorded SHA-256'):
            record.check_record(record.load_entries(out), svg.parent, self.base)


def git(folder, *args):
    result = subprocess.run(['git', '-C', str(folder), *args], capture_output=True, text=True, timeout=60)
    if result.returncode:
        raise AssertionError(result.stderr)
    return result.stdout.strip()


class GitRecordTests(FinishedBatch):
    def setUp(self):
        super().setUp()
        self.origin = self.root / 'origin.git'
        subprocess.run(['git', 'init', '--quiet', '--bare', '-b', 'main', str(self.origin)], check=True)
        self.repo = self.root / 'repo'
        subprocess.run(['git', 'clone', '--quiet', str(self.origin), str(self.repo)], check=True, capture_output=True)
        for key, value in (('user.name', 'Test'), ('user.email', 't@example.com'), ('commit.gpgsign', 'false')):
            git(self.repo, 'config', key, value)
        migrations = self.repo / batch_record.MIGRATIONS
        migrations.mkdir(parents=True)
        (migrations / 'migration_db.py').write_text('# placeholder\n')
        (self.repo / 'notes.txt').write_text('one\n')
        git(self.repo, 'add', '.')
        git(self.repo, 'commit', '--quiet', '-m', 'start')
        git(self.repo, 'push', '--quiet', '-u', 'origin', 'main')
        # Unrelated work in the user's own folder: an edit and a staged file.
        (self.repo / 'notes.txt').write_text('two\n')
        (self.repo / 'staged.txt').write_text('staged\n')
        git(self.repo, 'add', 'staged.txt')
        self.state['base'] = str(self.base)

    def answers(self, *values):
        values = list(values)
        return lambda prompt: values.pop(0)

    def manifest_now(self):
        return json.loads((Path(self.manifest['folder']) / 'manifest.json').read_text(encoding='utf-8'))

    def test_commit_holds_only_the_record_and_leaves_the_folder_alone(self):
        batch_record.record_batch(self.manifest, self.state, self.answers('group-basics', 'COMMIT'), root=self.repo)
        saved = self.manifest_now()['record']
        date = record.published_on(self.manifest)
        branch = f'entries/{date.isoformat()}-group-basics'
        self.assertEqual((saved['state'], saved['branch']), ('pushed', branch))
        files = git(self.origin, 'show', '--name-only', '--format=', branch).splitlines()
        stem = f'add_group_basics_entries_{date.strftime("%Y%m%d")}'
        self.assertEqual(files[0], f'{batch_record.MIGRATIONS}/{stem}.py')
        self.assertEqual(len(files), 2)
        self.assertTrue(files[1].startswith(f'{batch_record.MIGRATIONS}/batch_diagrams/{stem}/'))
        self.assertEqual(git(self.origin, 'rev-parse', branch + '^'), git(self.origin, 'rev-parse', 'main'))
        self.assertEqual(git(self.repo, 'rev-parse', '--abbrev-ref', 'HEAD'), 'main')
        self.assertIn('A  staged.txt', git(self.repo, 'status', '--porcelain'))
        self.assertIn('M notes.txt', git(self.repo, 'status', '--porcelain'))
        self.assertFalse((Path(self.manifest['folder']) / 'git').exists())

    def test_anything_but_commit_commits_nothing(self):
        batch_record.record_batch(self.manifest, self.state, self.answers('group-basics', 'no'), root=self.repo)
        self.assertEqual(self.manifest_now()['record']['state'], 'planned')
        self.assertNotIn('entries/', git(self.origin, 'branch', '--list'))

    def test_failed_push_is_retried_without_a_second_commit(self):
        git(self.repo, 'remote', 'set-url', '--push', 'origin', str(self.root / 'missing.git'))
        with self.assertRaisesRegex(ValueError, 'git push failed'):
            batch_record.record_batch(self.manifest, self.state, self.answers('group-basics', 'COMMIT'), root=self.repo)
        saved = self.manifest_now()
        self.assertEqual(saved['record']['state'], 'committed')
        git(self.repo, 'remote', 'set-url', '--push', 'origin', str(self.origin))
        batch_record.record_batch(saved, self.state, self.answers(), root=self.repo)  # No questions asked again.
        branch = saved['record']['branch']
        self.assertEqual(git(self.origin, 'rev-parse', branch), saved['record']['commit'])
        self.assertEqual(git(self.origin, 'rev-list', '--count', 'main..' + branch), '1')

    def test_a_migration_already_on_main_is_refused(self):
        date = record.published_on(self.manifest)
        name = f'add_group_basics_entries_{date.strftime("%Y%m%d")}.py'
        other = self.root / 'other'
        subprocess.run(['git', 'clone', '--quiet', str(self.origin), str(other)], check=True, capture_output=True)
        git(other, 'config', 'user.name', 'T')
        git(other, 'config', 'user.email', 't@example.com')
        (other / batch_record.MIGRATIONS / name).write_text('# by hand\n')
        git(other, 'add', '.')
        git(other, 'commit', '--quiet', '-m', 'by hand')
        git(other, 'push', '--quiet')
        with self.assertRaisesRegex(ValueError, 'main already has'):
            batch_record.record_batch(self.manifest, self.state, self.answers('group-basics'), root=self.repo)

    def test_unverified_or_unsynchronized_batch_is_refused(self):
        self.manifest['synchronization'] = None
        with self.assertRaisesRegex(ValueError, 'option 8'):
            batch_record.record_batch(self.manifest, self.state, self.answers(), root=self.repo)

    def test_bad_topic_is_refused(self):
        with self.assertRaisesRegex(ValueError, 'lowercase'):
            batch_record.record_batch(self.manifest, self.state, self.answers('Group Basics'), root=self.repo)

    def test_menu_lists_finished_batches(self):
        with patch('builtins.print') as shown:
            batch_record.run(self.state, self.answers(''))
        text = ' '.join(str(c.args[0]) for c in shown.call_args_list if c.args)
        self.assertIn('"group basics"', text)
        self.assertIn('not recorded yet', text)

    def test_pull_request_link(self):
        git(self.repo, 'remote', 'set-url', 'origin', 'https://github.com/riskassure/chi-portfolio.git')
        self.assertEqual(batch_record.pull_request_link(self.repo, 'entries/2026-10-30-x'),
                         'https://github.com/riskassure/chi-portfolio/compare/main...entries/2026-10-30-x?expand=1')


if __name__ == '__main__':
    unittest.main()
