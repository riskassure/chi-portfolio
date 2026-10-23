from contextlib import closing
import hashlib
import json
import os
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
import diagram_sync
import diagram_recovery
from diagram_sync import build_payload, cleanup, render_missing, write_package
from inspect_staged_package import preview
from live_math_publication import publish
import preflight_live_package
import publish_staged_package
from preview_math_sync import read_snapshot
from services.math.render_helper import hash_pstricks_block
from test_diagram_sync import FIGURE, PICTURE, SVG, TREE, create_db, svg_for

SOURCE = Path(__file__).resolve().parents[1] / 'src'


class Interrupted(Exception):
    pass


def link_or_copy(source, target):
    """Point target at source; copy instead where symlinks need privileges (Windows without Developer Mode)."""
    try:
        os.symlink(source, target, target_is_directory=True)
    except (OSError, NotImplementedError):
        shutil.copytree(source, target, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))


class DiagramPublishTests(unittest.TestCase):
    """The server half: files first, rows in one transaction, a journal, and safe retries."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.laptop = root / 'laptop'
        self.laptop_diagrams = self.laptop / 'diagrams'
        self.laptop_diagrams.mkdir(parents=True)
        # Same layout as the host: <home>/chi-portfolio/backend/portfolio.db and <home>/backups.
        self.home = root / 'home'
        self.backend = self.home / 'chi-portfolio' / 'backend'
        self.live_diagrams = self.backend / 'data' / 'math' / 'diagrams'
        self.live_diagrams.mkdir(parents=True)
        self.live = self.backend / 'portfolio.db'
        self.backups = self.home / 'backups'
        link_or_copy(SOURCE, self.backend / 'src')

    def tearDown(self):
        self.temp.cleanup()

    def package(self, base_tex, working_tex=None, rows=(), live_files=None):
        """Build a package on the 'laptop' and a matching live database; return its bytes."""
        base = self.laptop / 'base.db'
        base.unlink(missing_ok=True)
        create_db(base, base_tex, rows)
        for source in rows:
            (self.laptop_diagrams / self.name(source)).write_bytes(svg_for(source))
        working = self.laptop / 'working.db'
        shutil.copyfile(base, working)
        for path in self.laptop_diagrams.iterdir():
            if path.name not in {self.name(source) for source in rows}:
                path.unlink()
        if working_tex is not None:
            with closing(sqlite3.connect(working)) as db:
                if base_tex is None:
                    db.execute("INSERT INTO math_concepts VALUES(1,'RootedTree','rooted-tree','rooted tree','chi',?,1,'','t','t')",
                               (working_tex,))
                    db.execute('INSERT INTO math_concept_classifications VALUES(1,1)')
                    db.execute('INSERT INTO math_concept_types VALUES(1,1)')
                else:
                    db.execute('UPDATE math_concepts SET cleaned_tex=?', (working_tex,))
                db.commit()
        render_missing(working, 'RootedTree', self.laptop_diagrams, svg_for)
        payload, files = build_payload(base, working, 'RootedTree', self.laptop_diagrams)
        shutil.copyfile(base, self.live)
        for source in rows:
            (self.live_diagrams / self.name(source)).write_bytes((live_files or {}).get(source, svg_for(source)))
        self.working = working
        output = self.laptop / ('package-' + os.urandom(4).hex() + '.zip')
        return write_package(payload, files, output)

    @staticmethod
    def name(source):
        return hash_pstricks_block(source) + '.svg'

    def run_publish(self, data):
        return publish(data, self.live, self.backups, SOURCE)

    def journal(self, data):
        return json.loads((self.backups / 'diagram-publish' / (hashlib.sha256(data).hexdigest() + '.json')).read_text())

    def live_state(self):
        with closing(sqlite3.connect(self.live)) as db:
            rows = db.execute('SELECT source_hash, source_tex, svg_path FROM math_concept_diagrams ORDER BY source_hash').fetchall()
            rendered = db.execute('SELECT rendered_tex FROM math_concepts').fetchall()
        return read_snapshot(self.live), rows, rendered

    def assert_no_dangling_rows(self):
        with closing(sqlite3.connect(self.live)) as db:
            for (path,) in db.execute('SELECT svg_path FROM math_concept_diagrams'):
                self.assertTrue((self.live_diagrams / path.rsplit('/', 1)[-1]).is_file(), path)

    def test_missing_svg_entry_published_then_already_present(self):
        data = self.package('A rooted tree:\n' + TREE)
        self.assertIn('EXPECTED TEXT MATCHES', preview(data, self.live, live=True))
        result = self.run_publish(data)
        self.assertEqual(result['status'], 'APPLIED')
        self.assertEqual((self.live_diagrams / self.name(TREE)).read_bytes(), svg_for(TREE))
        snapshot, rows, rendered = self.live_state()
        self.assertEqual(snapshot['RootedTree'], read_snapshot(self.working)['RootedTree'])
        self.assertEqual(rows, [(hash_pstricks_block(TREE), TREE, '/api/math/diagrams/' + self.name(TREE))])
        self.assertIn('/api/math/diagrams/' + self.name(TREE), rendered[0][0])
        self.assertNotIn('unavailable', rendered[0][0])
        journal = self.journal(data)
        self.assertEqual(journal['status'], 'COMMITTED')
        self.assertEqual(journal['files'][self.name(TREE)], dict(sha256=hashlib.sha256(svg_for(TREE)).hexdigest(),
                                                                 pre_existing=False, state='placed'))
        with closing(sqlite3.connect(result['backup'])) as backup:
            self.assertEqual(backup.execute('SELECT count(*) FROM math_concept_diagrams').fetchone()[0], 0)
        self.assertFalse((self.backend / 'data' / 'math' / 'diagrams-incoming').exists() and
                         any((self.backend / 'data' / 'math' / 'diagrams-incoming').iterdir()))
        self.assertIn('ALREADY PRESENT', preview(data, self.live, live=True))
        self.assertEqual(self.run_publish(data)['status'], 'ALREADY_PRESENT')

    def test_changed_diagram_replaces_rows_and_keeps_old_file(self):
        changed = PICTURE.replace('(2,2)\\end', '(1,2)\\end')
        data = self.package('Intro. ' + PICTURE + ' ' + FIGURE, 'New intro. ' + changed + ' ' + FIGURE, rows=[PICTURE])
        self.run_publish(data)
        snapshot, rows, _ = self.live_state()
        self.assertEqual([r[1] for r in rows], [changed])
        self.assertTrue(snapshot['RootedTree']['cleaned_tex'].startswith('New intro.'))
        self.assertEqual((self.live_diagrams / self.name(PICTURE)).read_bytes(), svg_for(PICTURE))
        self.assert_no_dangling_rows()

    def test_new_entry_with_diagram_and_duplicate_refused(self):
        data = self.package(None, 'A tree. ' + TREE)
        self.assertIn('NO DUPLICATE FOUND', preview(data, self.live, live=True))
        self.assertEqual(self.run_publish(data)['status'], 'APPLIED')
        self.assertEqual(read_snapshot(self.live)['RootedTree']['cleaned_tex'], 'A tree. ' + TREE)
        self.assert_no_dangling_rows()
        with closing(sqlite3.connect(self.live)) as db:
            db.execute("UPDATE math_concepts SET canonical_name='Other', slug='other'")
            db.commit()
        self.assertIn('BLOCKED', preview(data, self.live, live=True))
        with self.assertRaisesRegex(ValueError, 'Duplicate title'):
            self.run_publish(data)

    def test_live_conflicts_refused_before_any_file_is_written(self):
        data = self.package('Intro. ' + PICTURE, 'Intro. ' + TREE, rows=[PICTURE])
        with closing(sqlite3.connect(self.live)) as db:
            db.execute("UPDATE math_concept_diagrams SET source_tex=source_tex || ' '")
            db.commit()
        self.assertIn('CONFLICT — stored diagram rows differ', preview(data, self.live, live=True))
        with self.assertRaisesRegex(ValueError, 'stored diagram rows differ'):
            self.run_publish(data)
        self.assertFalse((self.live_diagrams / self.name(TREE)).exists())
        self.assertEqual(list((self.backups / 'diagram-publish').glob('*.json')), [])  # Only the lock file.
        with closing(sqlite3.connect(self.live)) as db:
            db.execute("UPDATE math_concepts SET cleaned_tex='Edited live.'")
            db.commit()
        self.assertIn('CONFLICT', preview(data, self.live, live=True))

    def test_different_valid_live_file_is_kept_and_unusable_one_stops(self):
        data = self.package('A rooted tree:\n' + TREE)
        live_copy = SVG.replace('57', '58').encode()
        (self.live_diagrams / self.name(TREE)).write_bytes(live_copy)
        self.assertIn('which will be kept', preview(data, self.live, live=True))
        result = self.run_publish(data)
        self.assertEqual(result['kept_live_copies'], [self.name(TREE)])
        self.assertEqual((self.live_diagrams / self.name(TREE)).read_bytes(), live_copy)
        self.assertEqual(self.journal(data)['files'][self.name(TREE)]['pre_existing'], True)
        data = self.package('A rooted tree:\n' + TREE)
        (self.live_diagrams / self.name(TREE)).write_bytes(b'<svg broken')
        self.assertIn('CONFLICT — unusable diagram file', preview(data, self.live, live=True))
        with self.assertRaisesRegex(ValueError, 'unusable'):
            self.run_publish(data)
        self.assertEqual((self.live_diagrams / self.name(TREE)).read_bytes(), b'<svg broken')
        self.assertEqual(self.live_state()[1], [])

    def test_interruption_at_every_step_then_retry(self):
        name = self.name(TREE)
        for step in ('journal', 'incoming:' + name, 'placed:' + name, 'files', 'backup', 'rows'):
            with self.subTest(step):
                shutil.rmtree(self.backups, ignore_errors=True)
                for path in self.live_diagrams.iterdir():
                    path.unlink()
                data = self.package('A rooted tree:\n' + TREE)
                before = self.live_state()

                def stop(reached, step=step):
                    if reached == step:
                        raise Interrupted(step)
                with patch.object(diagram_sync, '_checkpoint', side_effect=stop):
                    with self.assertRaises(Interrupted):
                        self.run_publish(data)
                # Database untouched; any file left is complete, unused and recorded.
                self.assertEqual(self.live_state(), before)
                if (self.live_diagrams / name).exists():
                    self.assertEqual((self.live_diagrams / name).read_bytes(), svg_for(TREE))
                    plan = cleanup(self.backups / 'diagram-publish' / (hashlib.sha256(data).hexdigest() + '.json'),
                                   self.live, self.live_diagrams)
                    self.assertEqual(plan['unused_files'], [name] if step != 'incoming:' + name else [])
                self.assertEqual(sorted(p.name for p in self.live_diagrams.iterdir()),
                                 [] if step in ('journal', 'incoming:' + name) else [name])
                self.assertIn('EXPECTED TEXT MATCHES', preview(data, self.live, live=True))
                self.assertEqual(self.run_publish(data)['status'], 'APPLIED')
                self.assertEqual(self.journal(data)['status'], 'COMMITTED')
                self.assertEqual(self.journal(data)['files'][name]['pre_existing'], False)
                self.assert_no_dangling_rows()

    def test_interruption_after_commit_reports_already_present(self):
        data = self.package('A rooted tree:\n' + TREE)
        with patch.object(diagram_sync, '_checkpoint', side_effect=lambda step: (_ for _ in ()).throw(Interrupted())
                          if step == 'committed' else None):
            with self.assertRaises(Interrupted):
                self.run_publish(data)
        self.assertIn('ALREADY PRESENT', preview(data, self.live, live=True))
        self.assertEqual(self.run_publish(data)['status'], 'ALREADY_PRESENT')

    def test_cleanup_removes_only_unreferenced_files_this_publish_created(self):
        data = self.package('Intro. ' + PICTURE + ' and ' + TREE, rows=[PICTURE])
        journal_path = self.backups / 'diagram-publish' / (hashlib.sha256(data).hexdigest() + '.json')
        result = self.run_publish(data)
        self.assertEqual(cleanup(journal_path, self.live, self.live_diagrams)['unused_files'], [])
        other = self.incoming() / ('a' * 32)  # Not this publish's folder.
        other.mkdir(parents=True)
        (other / self.name(TREE)).write_bytes(b'<svg partial')
        shutil.copyfile(result['backup'], self.live)  # Undo the publish from its backup.
        plan = cleanup(journal_path, self.live, self.live_diagrams)
        self.assertEqual((plan['unused_files'], plan['incoming_folders'], plan['other_incoming_folders']),
                         ([self.name(TREE)], [], ['a' * 32]))
        self.assertFalse(plan['removed'])
        self.assertTrue((self.live_diagrams / self.name(TREE)).exists())
        cleanup(journal_path, self.live, self.live_diagrams, remove=True)
        self.assertFalse((self.live_diagrams / self.name(TREE)).exists())
        self.assertTrue(other.exists())  # Another publish's folder is never removed.
        self.assertTrue((self.live_diagrams / self.name(PICTURE)).exists())  # Existed before; never touched.
        self.assertEqual(json.loads(journal_path.read_text())['cleaned'][0]['files'], [self.name(TREE)])

    def incoming(self):
        return self.backend / 'data' / 'math' / 'diagrams-incoming'

    def test_cleanup_removes_only_incoming_folders_its_journal_recorded(self):
        # Two interrupted publishes, each crashing before it could tidy its incoming folder.
        first = self.package('A rooted tree:\n' + TREE)
        name = self.name(TREE)
        with patch.object(diagram_sync, '_checkpoint', side_effect=lambda step: (_ for _ in ()).throw(Interrupted())
                          if step == 'incoming:' + name else None), \
                patch.object(diagram_sync.shutil, 'rmtree'):
            with self.assertRaises(Interrupted):
                self.run_publish(first)
        mine = self.journal(first)['incoming']
        self.assertEqual(len(mine), 1)
        other = self.incoming() / ('b' * 32)
        other.mkdir()
        (other / name).write_bytes(svg_for(TREE))
        # Chi's reproduction: cleanup with a journal that recorded no folder removes nothing.
        empty = self.backups / 'diagram-publish' / ('0' * 64 + '.json')
        empty.write_text(json.dumps(dict(status='FILES_PENDING', files={})))
        plan = cleanup(empty, self.live, self.live_diagrams, remove=True)
        self.assertEqual((plan['incoming_folders'], plan['other_incoming_folders']), ([], sorted(mine + ['b' * 32])))
        self.assertTrue((self.incoming() / mine[0]).is_dir() and other.is_dir())
        plan = cleanup(self.backups / 'diagram-publish' / (hashlib.sha256(first).hexdigest() + '.json'),
                       self.live, self.live_diagrams, remove=True)
        self.assertEqual((plan['incoming_folders'], plan['other_incoming_folders']), (mine, ['b' * 32]))
        self.assertFalse((self.incoming() / mine[0]).exists())
        self.assertTrue(other.is_dir())

    def test_recovery_cannot_run_while_a_publish_is_between_placing_and_committing(self):
        data = self.package('A rooted tree:\n' + TREE)
        journal_path = self.backups / 'diagram-publish' / (hashlib.sha256(data).hexdigest() + '.json')
        name, attempts = self.name(TREE), []

        def recover(step):
            # The file is placed but no row references it yet: exactly when cleanup would delete it.
            if step == 'files':
                with self.assertRaisesRegex(ValueError, 'Another diagram publish or recovery is running'):
                    cleanup(journal_path, self.live, self.live_diagrams, remove=True)
                attempts.append(step)
        with patch.object(diagram_sync, 'LOCK_WAIT', 0.3), patch.object(diagram_sync, '_checkpoint', side_effect=recover):
            self.assertEqual(self.run_publish(data)['status'], 'APPLIED')
        self.assertEqual(attempts, ['files'])
        self.assertTrue((self.live_diagrams / name).is_file())
        self.assert_no_dangling_rows()
        self.assertNotIn('cleaned', self.journal(data))
        # Once the publish is done, recovery sees the row and leaves the file alone.
        self.assertEqual(cleanup(journal_path, self.live, self.live_diagrams, remove=True)['unused_files'], [])
        self.assertTrue((self.live_diagrams / name).is_file())

    def test_publish_waits_for_recovery_and_gives_up_cleanly(self):
        data = self.package('A rooted tree:\n' + TREE)
        before = self.live_state()
        with patch.object(diagram_sync, 'LOCK_WAIT', 0.3), diagram_sync.publish_lock(self.backups / 'diagram-publish'):
            with self.assertRaisesRegex(ValueError, 'Another diagram publish or recovery is running'):
                self.run_publish(data)
        self.assertEqual(self.live_state(), before)
        self.assertEqual(list(self.live_diagrams.iterdir()), [])
        self.assertFalse((self.backups / 'diagram-publish' / (hashlib.sha256(data).hexdigest() + '.json')).exists())
        self.assertEqual(self.run_publish(data)['status'], 'APPLIED')

    def test_cleanup_holds_the_database_write_lock_while_deleting(self):
        data = self.package('A rooted tree:\n' + TREE)
        journal_path = self.backups / 'diagram-publish' / (hashlib.sha256(data).hexdigest() + '.json')
        with patch.object(diagram_sync, '_checkpoint', side_effect=lambda step: (_ for _ in ()).throw(Interrupted())
                          if step == 'files' else None):
            with self.assertRaises(Interrupted):
                self.run_publish(data)
        seen = []
        real_unlink = Path.unlink

        def unlink(path, *args, **kwargs):
            # Another writer trying to start a transaction mid-deletion must be refused.
            with closing(sqlite3.connect(self.live, timeout=0)) as other:
                with self.assertRaises(sqlite3.OperationalError):
                    other.execute('BEGIN IMMEDIATE')
            seen.append(path.name)
            return real_unlink(path, *args, **kwargs)
        with patch.object(Path, 'unlink', unlink):
            cleanup(journal_path, self.live, self.live_diagrams, remove=True)
        self.assertEqual(seen, [self.name(TREE)])

    def test_preflight_and_recovery_scripts_run_with_their_shipped_modules(self):
        data = self.package('A rooted tree:\n' + TREE)
        package = self.laptop / 'staged.zip'
        package.write_bytes(data)
        request = preflight_live_package.build_request('cwoo', '/home/cwoo/chi-portfolio-staging/' + 'a' * 32 + '/package.zip', package)
        request.update(remote=str(package), database=str(self.live))
        before = hashlib.sha256(self.live.read_bytes()).digest()
        result = subprocess.run([sys.executable, '-I', '-B', '-c', preflight_live_package.BOOTSTRAP],
                                input=json.dumps(request), capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('EXPECTED TEXT MATCHES', result.stdout)
        self.assertEqual(before, hashlib.sha256(self.live.read_bytes()).digest())
        request['modules'].append(('live_math_publication',
                                  (SOURCE.parent / 'live_math_publication.py').read_text(encoding='utf-8')))
        result = subprocess.run([sys.executable, '-I', '-B', '-c', publish_staged_package.BOOTSTRAP],
                                input=json.dumps(request), capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout.split('PUBLICATION_RESULT=')[1])['status'], 'APPLIED')
        self.assert_no_dangling_rows()
        for package_sha, expected in ((None, 'COMMITTED'), (hashlib.sha256(data).hexdigest(), [])):
            request = diagram_recovery.build_request('cwoo', package_sha, False)
            request['database'] = str(self.live)
            result = subprocess.run([sys.executable, '-I', '-B', '-c', diagram_recovery.BOOTSTRAP],
                                    input=json.dumps(request), capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(result.returncode, 0, result.stderr)
            answer = json.loads(result.stdout.split('RECOVERY_RESULT=')[1])
            self.assertEqual(answer[0]['status'] if package_sha is None else answer['unused_files'], expected)
        with self.assertRaises(ValueError):
            diagram_recovery.build_request('cwoo', None, True)
        with self.assertRaises(ValueError):
            diagram_recovery.build_request('cwoo', '../x', False)


class WorkflowRouteTests(unittest.TestCase):
    """Options 1 and 2 route diagram changes through the diagram package."""

    def test_option_1_lists_diagram_changes_and_option_2_packages_them(self):
        import website_workflow as helper
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            diagrams = root / 'diagrams'
            diagrams.mkdir()
            base, working = root / 'base.db', root / 'working.db'
            create_db(base, 'A rooted tree:\n' + TREE)
            shutil.copyfile(base, working)
            state = dict(base=str(base), base_sha256=helper.digest(base), working=str(working), username='cwoo', job=None)
            with patch.object(helper, 'ROOT', root), patch.object(helper, 'DIAGRAMS', diagrams), \
                    patch.object(helper, 'save'):
                self.assertEqual(helper.changed_entries(state), [])  # Untouched entries are not listed.
                with closing(sqlite3.connect(working)) as db:
                    db.execute("UPDATE math_concepts SET cleaned_tex='A rooted tree, fixed:\n' || ?", (TREE,))
                    db.commit()
                [item] = helper.changed_entries(state)
                self.assertFalse(item['diagrams'])
                self.assertIn('choose 19 to render them', item['reason'])
                with patch.object(diagram_sync, 'render_svg', side_effect=svg_for):
                    self.assertIn('Rendered: ' + hash_pstricks_block(TREE) + '.svg',
                                  helper.render_missing_diagrams(state, 'RootedTree'))
                [item] = helper.changed_entries(state)
                self.assertEqual((item['diagrams'], item['supported'], item['fields']), (True, True, ['cleaned_tex', 'diagrams']))
                report = helper.prepare_selected(state, 'RootedTree')
                self.assertIn('change existing entry diagrams and text', report)
                self.assertEqual(state['job']['proposed'], read_snapshot(working)['RootedTree'])
                self.assertEqual(helper.current_job(state)['canonical'], 'RootedTree')
                with closing(sqlite3.connect(working)) as db:
                    db.execute("UPDATE math_concepts SET cleaned_tex=? || ' \\includegraphics{x.png}'", (TREE,))
                    db.commit()
                [item] = helper.changed_entries(state)
                self.assertIn('other images and embeds must stay', item['reason'])


if __name__ == '__main__':
    unittest.main()
