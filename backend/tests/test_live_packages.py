import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import live_packages as packages

REQUIREMENTS = (packages.ROOT / packages.REQUIREMENTS).read_text(encoding='utf-8')


def digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


class RequirementsTests(unittest.TestCase):
    def test_real_requirements_file_is_exact_pins(self):
        pins = packages.parse_requirements(REQUIREMENTS)
        self.assertIn('Flask', pins)
        self.assertIn('zxcvbn', pins)

    def test_anything_but_exact_pins_is_refused(self):
        for text in ['Flask>=3.0\n', 'Flask\n', '-e .\n', 'https://example.com/x.whl\n', '# only a comment\n',
                     'Flask==3.1.3\nflask==3.1.4\n']:
            with self.assertRaises(ValueError, msg=text):
                packages.parse_requirements(text)

    def test_differences_ignore_name_spelling(self):
        wanted = {'Jinja2': '3.1.6', 'MarkupSafe': '3.0.3', 'zxcvbn': '4.5.0'}
        installed = {'jinja2': '3.1.6', 'markupsafe': '3.0.2', 'pip': '25.0'}
        self.assertEqual(packages.differences(wanted, installed),
                         [('MarkupSafe', '3.0.2', '3.0.3'), ('zxcvbn', None, '4.5.0')])


class RunTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.folder = Path(folder.name)
        settings = self.folder / 'api.json'
        settings.write_text(json.dumps(dict(username='cwoo', token='dummy-token')), encoding='utf-8')
        patcher = patch.object(packages, 'SETTINGS', settings)
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch.object(packages.site_deployment, 'domains', return_value=['www.cwoo.me'])
        patcher.start()
        self.addCleanup(patcher.stop)
        self.pins = packages.parse_requirements(REQUIREMENTS)
        self.reloads, self.verified, self.calls = [], [], []

    def run_option(self, answers, installed_before, installed_after=None, copy=None):
        def call(username, request, timeout):
            self.calls.append(request)
            if request['mode'] == 'list':
                return dict(python='/home/cwoo/.virtualenvs/chi-portfolio/bin/python', installed=installed_before,
                            copy=digest(REQUIREMENTS) if copy is None else copy)
            self.assertEqual(request['requirements'], REQUIREMENTS)
            return dict(python='x', installed=installed_after, copy=digest(REQUIREMENTS))
        answers = iter(answers)
        with patch('builtins.print'):
            packages.run(dict(username='cwoo'), ask=lambda prompt: next(answers), guard=lambda root, paths: 'a' * 40,
                         call=call, reload=lambda settings, domain: self.reloads.append(domain),
                         verify=self.verified.append, receipts=self.folder / 'receipts')

    def receipts(self):
        return [json.loads(path.read_text(encoding='utf-8')) for path in sorted((self.folder / 'receipts').glob('*.json'))]

    def test_nothing_to_do_changes_nothing(self):
        self.run_option([], dict(self.pins))
        self.assertEqual([request['mode'] for request in self.calls], ['list'])
        self.assertFalse((self.folder / 'receipts').exists())

    def test_cancel_changes_nothing(self):
        old = dict(self.pins, Flask='3.0.0')
        self.run_option(['no'], old)
        self.assertEqual([request['mode'] for request in self.calls], ['list'])
        self.assertEqual(self.reloads, [])

    def test_update_installs_reloads_and_records(self):
        old = dict(self.pins, Flask='3.0.0')
        self.run_option(['UPDATE'], old, dict(self.pins))
        self.assertEqual([request['mode'] for request in self.calls], ['list', 'install'])
        self.assertEqual(self.reloads, ['www.cwoo.me'])
        self.assertEqual(self.verified, ['www.cwoo.me'])
        receipt, = self.receipts()
        self.assertEqual(receipt['status'], 'HOMEPAGE_VERIFIED')
        self.assertEqual(receipt['changes'], [dict(name='Flask', before='3.0.0', after=self.pins['Flask'])])

    def test_copy_only_update_skips_reload(self):
        self.run_option(['UPDATE'], dict(self.pins), dict(self.pins), copy='old')
        self.assertEqual(self.reloads, [])
        self.assertEqual(self.receipts()[0]['status'], 'COPY_UPDATED')

    def test_mismatch_after_install_stops_before_reload(self):
        old = dict(self.pins, Flask='3.0.0')
        with self.assertRaises(RuntimeError):
            self.run_option(['UPDATE'], old, old)
        self.assertEqual(self.reloads, [])
        self.assertEqual(self.receipts()[0]['status'], 'MISMATCH_AFTER_INSTALL')

    def test_guard_refusal_stops_before_connecting(self):
        def refuse(root, paths):
            self.assertEqual(paths, ['backend/requirements.txt'])
            raise ValueError('Deploy guard: not on main')
        with self.assertRaises(ValueError):
            packages.run(dict(username='cwoo'), guard=refuse, call=lambda *args: self.fail('connected'))


class RemoteTests(unittest.TestCase):
    def test_failed_or_garbled_ssh_is_reported(self):
        for result in [subprocess.CompletedProcess([], 1, packages.PREFIX + '{}\n'),
                       subprocess.CompletedProcess([], 0, 'no answer\n')]:
            with patch.object(packages.subprocess, 'run', return_value=result):
                with self.assertRaises(RuntimeError):
                    packages.remote('cwoo', dict(mode='list', virtualenv='chi-portfolio'), 10)

    def test_bad_username_never_connects(self):
        with patch.object(packages.subprocess, 'run') as run:
            with self.assertRaises(ValueError):
                packages.remote('-oProxyCommand=x', {}, 10)
            run.assert_not_called()


@unittest.skipUnless(os.name == 'posix', 'the server side runs on Linux')
class RemoteScriptTests(unittest.TestCase):
    """Run REMOTE_SCRIPT locally against a fake home whose 'virtualenv python' is a shell script."""

    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.home = Path(folder.name)
        self.copy = self.home / 'chi-portfolio' / 'backend' / 'requirements.txt'
        self.copy.parent.mkdir(parents=True)
        self.copy.write_bytes(b'Flask==3.0.0\r\n')
        python = self.home / '.virtualenvs' / 'chi-portfolio' / 'bin' / 'python'
        python.parent.mkdir(parents=True)
        python.write_text('#!/bin/sh\n'
                          'case "$3" in\n'
                          '  list) echo \'[{"name": "flask", "version": "3.0.0"}]\' ;;\n'
                          '  install) echo "pip says hello"; exit "$PIP_EXIT" ;;\n'
                          'esac\n')
        python.chmod(0o755)

    def script(self, request, pip_exit=0):
        return subprocess.run([sys.executable, '-I', '-B', '-c', packages.REMOTE_SCRIPT], input=json.dumps(request),
                              text=True, capture_output=True,
                              env=dict(os.environ, HOME=str(self.home), PIP_EXIT=str(pip_exit)))

    def answer(self, result):
        line, = [line for line in result.stdout.splitlines() if line.startswith(packages.PREFIX)]
        return json.loads(line[len(packages.PREFIX):])

    def test_list_ignores_line_endings_of_the_live_copy(self):
        answer = self.answer(self.script(dict(mode='list', virtualenv='chi-portfolio')))
        self.assertEqual(answer['installed'], {'flask': '3.0.0'})
        self.assertEqual(answer['copy'], digest('Flask==3.0.0\n'))

    def test_successful_install_replaces_the_live_copy(self):
        result = self.script(dict(mode='install', virtualenv='chi-portfolio', requirements='Flask==3.1.3\n'))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('pip says hello', result.stderr)
        self.assertEqual(self.copy.read_text(), 'Flask==3.1.3\n')
        self.assertEqual(sorted(p.name for p in self.home.iterdir()), ['.virtualenvs', 'chi-portfolio'])

    def test_failed_install_keeps_the_live_copy(self):
        result = self.script(dict(mode='install', virtualenv='chi-portfolio', requirements='Flask==3.1.3\n'), pip_exit=1)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn(packages.PREFIX, result.stdout)
        self.assertEqual(self.copy.read_bytes(), b'Flask==3.0.0\r\n')
        self.assertEqual(sorted(p.name for p in self.home.iterdir()), ['.virtualenvs', 'chi-portfolio'])


if __name__ == '__main__':
    unittest.main()
