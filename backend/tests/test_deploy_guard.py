from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import deploy_guard as guard
import website_workflow as helper


class DeployGuardTests(unittest.TestCase):
    """A real laptop clone of a bare 'GitHub' repository, so every git answer is genuine."""

    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name).resolve()
        self.github, self.repo, self.other = root/'github.git', root/'laptop', root/'other'
        self.run_git(root, 'init', '-q', '--bare', '-b', 'main', str(self.github))
        self.run_git(root, 'clone', '-q', str(self.github), str(self.repo))
        self.write('frontend/page.html', 'page\n')
        self.write('backend/src/routes/example.py', 'VALUE = 1\n')
        self.write('frontend/geography/places-data.js', 'places\n')
        self.commit('first')
        self.run_git(self.repo, 'push', '-q', 'origin', 'main')
        self.paths = ['frontend/page.html', 'backend/src/routes/example.py']

    def run_git(self, folder, *args):
        subprocess.run(['git', '-C', str(folder), '-c', 'user.name=t', '-c', 'user.email=t@example.com',
                        '-c', 'init.defaultBranch=main', *args], check=True, capture_output=True)

    def write(self, path, text, folder=None):
        target = (folder or self.repo)/path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding='utf-8')

    def commit(self, message, folder=None):
        self.run_git(folder or self.repo, 'add', '-A')
        self.run_git(folder or self.repo, 'commit', '-q', '-m', message)

    def check(self, paths=None):
        with patch('builtins.print'):
            return guard.check(self.repo, self.paths if paths is None else paths)

    def test_clean_main_matching_github_passes(self):
        commit = self.check()
        self.assertEqual(commit, subprocess.run(['git', '-C', str(self.repo), 'rev-parse', 'HEAD'],
                                                capture_output=True, text=True).stdout.strip())

    def test_other_branch_blocks(self):
        self.run_git(self.repo, 'switch', '-q', '-c', 'feature')
        with self.assertRaisesRegex(ValueError, 'on "feature", not main'):
            self.check()

    def test_uncommitted_change_blocks_and_names_the_file(self):
        self.write('backend/src/routes/example.py', 'VALUE = 2\n')
        with self.assertRaisesRegex(ValueError, 'not committed:\n  backend/src/routes/example.py'):
            self.check()

    def test_change_to_an_unselected_tracked_file_also_blocks(self):
        self.write('frontend/page.html', 'edited\n')
        with self.assertRaisesRegex(ValueError, 'frontend/page.html'):
            self.check(['backend/src/routes/example.py'])

    def test_behind_github_blocks(self):
        self.run_git(self.github.parent, 'clone', '-q', str(self.github), str(self.other))
        self.write('frontend/page.html', 'newer\n', self.other)
        self.commit('newer', self.other)
        self.run_git(self.other, 'push', '-q', 'origin', 'main')
        with self.assertRaisesRegex(ValueError, 'git pull'):
            self.check()

    def test_unpushed_commit_blocks(self):
        self.write('frontend/page.html', 'local only\n')
        self.commit('local only')
        with self.assertRaisesRegex(ValueError, 'not on GitHub'):
            self.check()

    def test_untracked_selected_file_blocks_but_other_untracked_files_do_not(self):
        self.write('frontend/new.js', 'new\n')
        self.write('notes.txt', 'scratch\n')
        self.assertTrue(self.check())
        with self.assertRaisesRegex(ValueError, 'part of main:\n  frontend/new.js'):
            self.check(['frontend/new.js'])

    def test_content_files_never_block(self):
        self.write('frontend/geography/places-data.js', 'new pin\n')
        self.assertTrue(self.check())
        self.run_git(self.repo, 'switch', '-q', '-c', 'feature')
        self.assertIsNone(self.check(['frontend/geography/places-data.js']))

    def test_unreachable_github_blocks(self):
        self.run_git(self.repo, 'remote', 'set-url', 'origin', str(self.github.parent/'missing.git'))
        with self.assertRaisesRegex(ValueError, 'Could not reach GitHub'):
            self.check()

    def test_option_14_records_the_commit_and_option_5_rechecks(self):
        state = dict(username='cwoo')
        with patch.object(helper, 'ROOT', self.repo), patch.object(helper, 'save'), \
             patch.object(helper.frontend_sync, 'capture_live', return_value={'page.html': 'older\n'}), \
             patch('builtins.print'):
            helper.prepare_frontend(state, ['page.html'])
            job = state['job']
            self.assertEqual(job['repo_paths'], ['frontend/page.html'])
            self.assertEqual(job['git_commit'], self.check())
            helper.guard_code_publication(job)
            self.write('frontend/page.html', 'edited after review\n')
            self.commit('edited after review')
            self.run_git(self.repo, 'push', '-q', 'origin', 'main')
            with self.assertRaisesRegex(ValueError, 'main has moved'):
                helper.guard_code_publication(job)
            del job['repo_paths']
            with self.assertRaisesRegex(ValueError, 'before the deploy guard'):
                helper.guard_code_publication(job)

    def test_option_5_stops_before_asking_to_publish(self):
        job = dict(kind='website-code', remote='remote', checked=True, canonical='Website code: x',
                   repo_paths=self.paths, git_commit='0'*40)
        with patch.object(helper, 'ROOT', self.repo), patch.object(helper, 'current_job', return_value=job), \
             patch.object(helper, 'publish_staged') as publish, patch('builtins.input') as ask, patch('builtins.print'):
            with self.assertRaisesRegex(ValueError, 'main has moved'):
                helper.publish_reviewed(dict(username='cwoo'))
        ask.assert_not_called()
        publish.assert_not_called()


if __name__ == '__main__':
    unittest.main()
