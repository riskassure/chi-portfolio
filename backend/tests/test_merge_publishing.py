"""Merging, retiring and undoing entries end to end (design v3 sections 5, 7 and 8).

Each test runs the helper's own steps on a baseline, working copy and live
database: start the session (reading live), publish the survivor's text,
prepare the merge package, check it as option 4 does, publish it as the
server does, record the receipt, and bring the result home with option 8.
Only SSH is left out: the live reads and publishes call the same functions
the server runs.
"""
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
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from math_fixture import make_catalog  # noqa: E402
from bring_changes_home import refresh  # noqa: E402
from inspect_staged_package import preview  # noqa: E402
from live_math_publication import publish  # noqa: E402
import merge_sync  # noqa: E402
import merge_workflow  # noqa: E402
from preview_math_sync import read_snapshot, read_status  # noqa: E402
from stage_pythonanywhere_package import read_package  # noqa: E402
from test_retirement_compat import SOURCE, zipped  # noqa: E402

A, S = 'MonoidWithInverses', 'Group'
NEW_TEXT = 'A group is a set with an associative operation, an identity and an inverse element for each element.'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def edit(path, sql, *args):
    with closing(sqlite3.connect(path)) as db:
        db.execute(sql, args)
        db.commit()


class MergeTrio(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.base, self.local, self.live = (self.root / name for name in ('base.db', 'working.db', 'live.db'))
        self.ids = make_catalog(self.base)
        shutil.copyfile(self.base, self.local)
        shutil.copyfile(self.base, self.live)
        self.state = dict(base=str(self.base), working=str(self.local), base_sha256=digest(self.base),
                          username='cwoo', job=None)
        self.save = Mock()
        # The live check reads the website code's contract beside the database (no symlink: Windows).
        contract = self.root / 'src' / 'services' / 'math' / 'retirement.py'
        contract.parent.mkdir(parents=True)
        shutil.copyfile(SOURCE / 'services' / 'math' / 'retirement.py', contract)

    # The helper's steps, with SSH replaced by the functions the server runs.
    def view(self, username, names):
        return json.loads(json.dumps(merge_sync.view(self.live, names, SOURCE)))

    def start(self, action='merge', absorbed=A, survivor=S, reason='The same definition twice.'):
        return merge_workflow.start_session(self.state, action, absorbed, survivor, reason, view=self.view,
                                            sessions=self.root / 'sessions')

    def publish_survivor_text(self, text=NEW_TEXT, title=None):
        """Edit S in the working copy and publish it with the options 2-5 patch (with a new title, when given)."""
        expected = read_snapshot(self.live)[S]
        edit(self.local, 'UPDATE math_concepts SET cleaned_tex = ? WHERE canonical_name = ?', text, S)
        details = {}
        if title:
            edit(self.local, 'UPDATE math_concepts SET title = ? WHERE canonical_name = ?', title, S)
            details = dict(replacement_title=title)
        data = zipped('patch.json', dict(canonical_name=S, expected=expected, replacement_tex=text, **details))
        self.assertEqual(publish(data, self.live, self.root / 'backups', SOURCE)['status'], 'APPLIED')

    def live_check(self):
        """Option 4: the verdict line of the live preflight report."""
        return preview(read_package(Path(self.state['job']['package'])), self.live, live=True).splitlines()[-3]

    def publish_job(self):
        """Option 5 for the active job, as publish_reviewed does after the server's publish."""
        job = self.state['job']
        result = publish(read_package(Path(job['package'])), self.live, self.root / 'backups', SOURCE)
        merge_workflow.record_receipt(self.state, job, result)
        return result

    def option_8(self):
        self.live.with_name('snapshot.json').write_text(json.dumps(dict(
            sha256=digest(self.live), source='/home/cwoo/chi-portfolio/backend/portfolio.db')))
        (self.root / 'diagrams').mkdir(exist_ok=True)
        with patch('bring_changes_home.diagram_home.stage_media', return_value=({}, {}, dict(
                verified=[], kept_local=[], missing_on_server=[]))), \
                patch('bring_changes_home.diagram_home.install_media'):
            return refresh(self.state, self.live, self.root / 'copies', Mock(), diagrams=self.root / 'diagrams')

    def merge(self, title=None):
        folder = self.start()
        self.publish_survivor_text(title=title)
        merge_workflow.prepare(self.state, self.save, folder)
        self.assertTrue(self.live_check().startswith('ELIGIBLE'), self.live_check())
        return folder, self.publish_job()

    def synced(self):
        result = self.option_8()
        self.assertTrue(result['safe'], result)
        self.assertEqual(digest(self.state['working']), digest(self.live))
        self.assertEqual(self.state['merge_pending_sync'], [])
        return result


class MergeTests(MergeTrio):
    def test_merge_publishes_and_option_8_brings_it_home(self):
        folder, result = self.merge()
        self.assertEqual(result['status'], 'APPLIED')
        status = read_status(self.live)
        self.assertEqual(status[A], dict(retired=True, retired_into=S, reason='The same definition twice.'))
        group = read_snapshot(self.live)[S]
        self.assertEqual(group['cleaned_tex'], NEW_TEXT)
        self.assertEqual(group['synonyms'], ['group alias', 'monoid with inverses'])
        self.assertEqual(group['definitions'], ['inverse element'])
        self.assertEqual(read_snapshot(self.live)[A], read_snapshot(self.base)[A])  # A itself is untouched.
        self.assertTrue((folder / 'receipt.json').exists())
        self.synced()

    def test_the_log_keeps_both_versions_of_the_survivor(self):
        folder, result = self.merge()
        with closing(sqlite3.connect(self.live)) as db:
            before, after = db.execute('SELECT survivor_before_json, survivor_after_json FROM math_concept_merges').fetchone()
            contract = db.execute('SELECT value FROM math_schema_meta').fetchone()[0]
        self.assertEqual(json.loads(before)['cleaned_tex'], 'A group is a set with an operation.')
        self.assertEqual(json.loads(after)['cleaned_tex'], NEW_TEXT)
        self.assertEqual(contract, '1')

    def test_an_unrelated_unpublished_local_edit_still_blocks_option_8(self):
        self.merge()
        edit(self.local, "UPDATE math_concepts SET cleaned_tex = 'Unpublished.' WHERE canonical_name = 'Subgroup'")
        working = digest(self.local)
        result = self.option_8()
        self.assertFalse(result['safe'])
        self.assertIn('math_concepts', result['blocked'])
        self.assertEqual(digest(self.local), working)
        self.assertEqual(len(self.state['merge_pending_sync']), 1)

    def test_an_unrelated_published_edit_is_brought_home_with_the_merge(self):
        self.merge()
        expected = read_snapshot(self.live)['Subgroup']
        edit(self.local, "UPDATE math_concepts SET cleaned_tex = 'Edited.' WHERE canonical_name = 'Subgroup'")
        publish(zipped('patch.json', dict(canonical_name='Subgroup', expected=expected, replacement_tex='Edited.')),
                self.live, self.root / 'backups', SOURCE)
        self.synced()

    def test_a_local_edit_to_a_value_the_receipt_sets_stops_option_8(self):
        self.merge()
        # A's retirement fields are what the receipt overwrites; a local value there must not vanish.
        edit(self.local, "UPDATE math_concepts SET retirement_reason = 'Local note.' WHERE canonical_name = ?", A)
        working = digest(self.local)
        with self.assertRaisesRegex(ValueError, "does not fit your local copy.*Local note"):
            self.option_8()
        self.assertEqual(digest(self.local), working)
        self.assertEqual(len(self.state['merge_pending_sync']), 1)

    def test_a_local_edit_beside_a_repointed_redirect_stops_option_8(self):
        edit(self.base, "UPDATE math_concepts SET retired_at = '2026-10-01', retired_into_id = ?, "
                        "retirement_reason = 'older' WHERE canonical_name = 'OldStub'", self.ids['monoid with inverses'])
        for path in (self.local, self.live):
            shutil.copyfile(self.base, path)
        self.state['base_sha256'] = digest(self.base)
        self.merge()
        edit(self.local, "UPDATE math_concepts SET retirement_reason = 'Local note.' WHERE canonical_name = 'OldStub'")
        result = self.option_8()
        self.assertFalse(result['safe'])
        self.assertIn('math_concepts', result['blocked'])

    def test_live_altered_after_the_merge_fails_the_receipt_check(self):
        self.merge()
        edit(self.live, 'DELETE FROM math_synonyms WHERE synonym_text = ?', 'monoid with inverses')
        with self.assertRaisesRegex(ValueError, 'lacks synonyms the merge added'):
            self.option_8()
        self.assertEqual(len(self.state['merge_pending_sync']), 1)

    def test_nothing_new_is_prepared_until_option_8(self):
        self.merge()
        with self.assertRaisesRegex(ValueError, 'waiting for option 8'):
            self.start('retire', 'OldStub', None, 'Unfinished.')
        self.synced()
        self.start('retire', 'OldStub', None, 'Unfinished.')

    def test_publishing_the_same_package_again_changes_nothing(self):
        folder, first = self.merge()
        live = digest(self.live)
        again = self.publish_job()
        self.assertEqual(again['status'], 'ALREADY_PRESENT')
        self.assertEqual(again['change_set'], first['change_set'])
        self.assertEqual(digest(self.live), live)
        self.assertEqual(len(self.state['merge_pending_sync']), 1)

    def test_redirects_into_the_absorbed_entry_are_repointed_and_undone(self):
        edit(self.base, "UPDATE math_concepts SET retired_at = '2026-10-01', retired_into_id = ?, "
                        "retirement_reason = 'older' WHERE canonical_name = 'OldStub'", self.ids['monoid with inverses'])
        for path in (self.local, self.live):
            shutil.copyfile(self.base, path)
        self.state['base_sha256'] = digest(self.base)
        folder, result = self.merge()
        self.assertEqual(result['change_set']['repointed'], ['OldStub'])
        self.assertEqual(read_status(self.live)['OldStub']['retired_into'], S)
        self.synced()
        merge_workflow.prepare_undo(self.state, self.save, folder)
        self.assertTrue(self.live_check().startswith('ELIGIBLE'), self.live_check())
        self.publish_job()
        self.assertEqual(read_status(self.live)['OldStub']['retired_into'], A)
        self.synced()


class SessionTests(MergeTrio):
    def test_the_live_reading_runs_in_an_isolated_interpreter_as_over_ssh(self):
        # The same bootstrap and module list SSH sends, run with -I so nothing comes from this checkout's path.
        site = self.root / 'site' / 'backend'
        (site / 'src' / 'services' / 'math').mkdir(parents=True)
        shutil.copyfile(SOURCE / 'services' / 'math' / 'retirement.py', site / 'src' / 'services' / 'math' / 'retirement.py')
        shutil.copyfile(self.live, site / 'portfolio.db')
        request = dict(merge_sync.view_request('cwoo', [A, S]), database=str(site / 'portfolio.db'))
        result = subprocess.run([sys.executable, '-I', '-B', '-c', merge_sync.VIEW_BOOTSTRAP], cwd=self.root,
                                input=json.dumps(request), capture_output=True, text=True, encoding='utf-8', timeout=120)
        self.assertEqual(result.returncode, 0, result.stderr)
        view = merge_sync.read_view(result.stdout)
        self.assertEqual((view['schema'], view['code_contract']), ('current', 1))
        self.assertEqual(view['entries'][A]['entry'], self.view('cwoo', [A])['entries'][A]['entry'])


    def test_session_refuses_unpublished_local_edits_to_either_entry(self):
        edit(self.local, "UPDATE math_concepts SET cleaned_tex = 'Local.' WHERE canonical_name = ?", S)
        with self.assertRaisesRegex(ValueError, 'differs from live'):
            self.start()

    def test_option_1_marks_a_local_retirement_edit_unsupported(self):
        import website_workflow
        edit(self.local, "UPDATE math_concepts SET retired_at = '2026-10-25', retirement_reason = 'x' "
                         "WHERE canonical_name = 'OldStub'")
        [item] = website_workflow.changed_entries(self.state)
        self.assertEqual((item['canonical'], item['fields'], item['supported']), ('OldStub', ['retirement'], False))
        self.assertIn('option 21', item['reason'])

    def test_survivor_must_be_edited_unless_metadata_only(self):
        folder = self.start()
        with self.assertRaisesRegex(ValueError, 'is unchanged'):
            merge_workflow.prepare(self.state, self.save, folder)
        merge_workflow.prepare(self.state, self.save, folder, metadata_only=True)
        self.assertTrue(self.live_check().startswith('ELIGIBLE'), self.live_check())

    def test_survivor_not_yet_published_is_a_conflict_and_nothing_changes(self):
        folder = self.start()
        edit(self.local, 'UPDATE math_concepts SET cleaned_tex = ? WHERE canonical_name = ?', NEW_TEXT, S)
        merge_workflow.prepare(self.state, self.save, folder)
        self.assertIn('CONFLICT', self.live_check())
        self.assertIn('Publish it with options 2-5 first', self.live_check())
        live = digest(self.live)
        with self.assertRaises(ValueError):
            self.publish_job()
        self.assertEqual(digest(self.live), live)
        self.assertEqual(read_status(self.live)[A]['retired'], False)

    def test_absorbed_entry_changed_on_live_after_the_session_started(self):
        folder = self.start()
        self.publish_survivor_text()
        merge_workflow.prepare(self.state, self.save, folder)
        edit(self.live, "UPDATE math_concepts SET cleaned_tex = 'Changed on live.' WHERE canonical_name = ?", A)
        self.assertIn('changed on live since the session started', self.live_check())

    def test_local_edit_after_preparing_stops_the_job(self):
        folder = self.start()
        self.publish_survivor_text()
        merge_workflow.prepare(self.state, self.save, folder)
        edit(self.local, "UPDATE math_concepts SET cleaned_tex = 'Again.' WHERE canonical_name = ?", S)
        from website_workflow import current_job
        with patch('website_workflow.digest', side_effect=lambda path: digest(path)):
            with self.assertRaisesRegex(ValueError, 'changed since preparation'):
                current_job(self.state)

    def test_live_code_must_declare_the_contract(self):
        folder = self.start()
        self.publish_survivor_text()
        merge_workflow.prepare(self.state, self.save, folder)
        old_code = self.root / 'old-src'
        (old_code / 'services' / 'math').mkdir(parents=True)
        status = merge_sync.status(self.live, merge_sync.unpack(read_package(Path(self.state['job']['package']))),
                                   '0' * 64, old_code)
        self.assertTrue(status.startswith('BLOCKED'), status)
        self.assertIn('option 15', status)

    def test_new_alias_clashes_refuse_and_existing_overlaps_are_only_recorded(self):
        # A's defined term "inverse element" is already a synonym of Subgroup: an existing overlap.
        edit(self.base, "INSERT INTO math_synonyms(concept_id, synonym_text) VALUES (?, 'inverse element')",
             self.ids['subgroup'])
        for path in (self.local, self.live):
            shutil.copyfile(self.base, path)
        self.state['base_sha256'] = digest(self.base)
        folder, result = self.merge()
        self.assertEqual([c['entry'] for c in result['change_set']['alias_warnings']], ['Subgroup'])
        self.synced()


class RetireAndUndoTests(MergeTrio):
    def test_plain_retirement_and_its_undo(self):
        folder = self.start('retire', 'OldStub', None, 'Unfinished test entry.')
        report = merge_workflow.prepare(self.state, self.save, folder)
        self.assertIn('related concept: Subgroup', report)
        self.assertTrue(self.live_check().startswith('ELIGIBLE'), self.live_check())
        self.publish_job()
        self.assertEqual(read_status(self.live)['OldStub'], dict(retired=True, retired_into=None,
                                                                 reason='Unfinished test entry.'))
        self.synced()
        merge_workflow.prepare_undo(self.state, self.save, folder)
        self.publish_job()
        self.assertFalse(read_status(self.live)['OldStub']['retired'])
        self.synced()

    def test_the_review_lists_explicit_links_to_the_retired_entry(self):
        edit(self.local, "UPDATE math_concepts SET cleaned_tex = 'See \\PMlinkname{the stub}{OldStub}.' "
                         "WHERE canonical_name = 'Group'")
        with closing(sqlite3.connect(self.local)) as db:
            self.assertEqual(merge_sync.incoming_links(db, 'OldStub'), dict(explicit=['Group'], related=['Subgroup']))

    def test_plain_retirement_is_refused_while_redirects_point_in(self):
        edit(self.live, "UPDATE math_concepts SET retired_at = '2026-10-01', retired_into_id = ?, "
                        "retirement_reason = 'older' WHERE canonical_name = 'OldStub'", self.ids['monoid with inverses'])
        with self.assertRaisesRegex(ValueError, 'would lose their redirect'):
            self.start('retire', A, None, 'Gone.')

    def test_undo_of_a_merge_removes_the_copies_and_option_8_brings_it_home(self):
        folder, _ = self.merge()
        self.synced()
        merge_workflow.prepare_undo(self.state, self.save, folder)
        self.assertTrue(self.live_check().startswith('ELIGIBLE'), self.live_check())
        self.publish_job()
        self.assertFalse(read_status(self.live)[A]['retired'])
        group = read_snapshot(self.live)[S]
        self.assertEqual((group['synonyms'], group['definitions'], group['cleaned_tex']),
                         (['group alias'], [], NEW_TEXT))  # The text stays; restoring it is a text edit.
        self.synced()

    def test_undo_is_refused_once_the_survivor_changed_its_copied_rows(self):
        folder, _ = self.merge()
        self.synced()
        edit(self.live, 'DELETE FROM math_definitions WHERE defined_term = ?', 'inverse element')
        merge_workflow.prepare_undo(self.state, self.save, folder)
        self.assertIn('CONFLICT', self.live_check())
        self.assertIn('is gone', self.live_check())

    def test_undo_rechecks_aliases_that_appeared_meanwhile(self):
        folder, _ = self.merge()
        self.synced()
        # Meanwhile another entry took the absorbed entry's title as its synonym.
        edit(self.live, "INSERT INTO math_synonyms(concept_id, synonym_text) VALUES (?, 'Monoid With Inverses')",
             self.ids['subgroup'])
        merge_workflow.prepare_undo(self.state, self.save, folder)
        self.assertIn('BLOCKED — Undo would create alias clashes', self.live_check())
        self.assertIn('Subgroup', self.live_check())

    def test_undo_waits_for_a_later_merge_into_the_survivor_to_be_undone(self):
        folder, _ = self.merge()
        self.synced()
        later = self.start('merge', 'OldStub', S, 'Also the same.')
        merge_workflow.prepare(self.state, self.save, later, metadata_only=True)
        self.publish_job()
        self.synced()
        merge_workflow.prepare_undo(self.state, self.save, folder)
        self.assertIn('Undo the later merge or retirement of OldStub first', self.live_check())


class MigrationTests(MergeTrio):
    """The git record: a migration written from the receipts rebuilds what live has."""

    def test_migration_from_the_receipts_matches_live(self):
        sys.path.insert(0, str(SOURCE / 'database' / 'math' / 'migrations'))
        import math_entry_merge
        from bring_changes_home import MATH_TABLES, inventory
        folder, _ = self.merge()
        self.synced()
        merge_workflow.prepare_undo(self.state, self.save, folder)
        self.publish_job()
        self.synced()
        script = self.root / 'merge_entries_test.py'
        math_entry_merge.write_migration(script, [folder / 'receipt.json', folder / 'undo-receipt.json'])
        namespace = {}
        exec(compile(script.read_text(encoding='utf-8'), str(script), 'exec'), namespace)
        rebuilt = self.root / 'rebuilt.db'
        shutil.copyfile(self.base, rebuilt)  # The catalog before the survivor's text edit and the merge.
        for _ in range(2):  # Running it again changes nothing.
            math_entry_merge.replay(rebuilt, namespace['CHANGE_SETS'])
        with closing(sqlite3.connect(rebuilt)) as mine, closing(sqlite3.connect(self.live)) as theirs:
            self.assertEqual(inventory(mine, MATH_TABLES)[1], inventory(theirs, MATH_TABLES)[1])

    def test_migration_replays_a_survivor_title_change(self):
        sys.path.insert(0, str(SOURCE / 'database' / 'math' / 'migrations'))
        import math_entry_merge
        from bring_changes_home import MATH_TABLES, inventory
        folder, _ = self.merge(title='group (algebra)')
        self.synced()
        script = self.root / 'merge_entries_title.py'
        math_entry_merge.write_migration(script, [folder / 'receipt.json'])
        namespace = {}
        exec(compile(script.read_text(encoding='utf-8'), str(script), 'exec'), namespace)
        rebuilt = self.root / 'rebuilt.db'
        shutil.copyfile(self.base, rebuilt)
        math_entry_merge.replay(rebuilt, namespace['CHANGE_SETS'])
        self.assertEqual(read_snapshot(rebuilt)[S]['title'], 'group (algebra)')
        with closing(sqlite3.connect(rebuilt)) as mine, closing(sqlite3.connect(self.live)) as theirs:
            self.assertEqual(inventory(mine, MATH_TABLES)[1], inventory(theirs, MATH_TABLES)[1])


if __name__ == '__main__':
    unittest.main()
