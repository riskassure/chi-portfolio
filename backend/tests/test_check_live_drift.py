import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import check_live_drift as drift


def run_reader_locally(live_root):
    """Stand-in for SSH: run the server-side reader against a local folder."""
    def reader(username, request):
        request = dict(request, root=str(live_root))
        result = subprocess.run([sys.executable, '-I', '-B', '-c', drift.READER], input=json.dumps(request),
                                text=True, encoding='utf-8', stdout=subprocess.PIPE, check=True)
        return drift.parse(result.stdout)
    return reader


class LiveDriftTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        base = Path(temp.name).resolve()
        self.repo, self.live, self.out = base/'repo', base/'live', base/'out'
        files = {
            '.gitignore': 'backend/*.db\nbackend/data/math/diagrams/*\n',
            'backend/src/app.py': 'print("app")\n',
            'backend/src/routes/math.py': 'ROUTE = 1\n',
            'frontend/index.html': '<p>home</p>\n',
            'frontend/geography/places-data.js': 'window.PLACES = [];\n',
            'backend/src/new_feature.py': 'NEW = 1\n',
            'docs/README.md': 'docs\n',
            'backend/tests/test_x.py': 'pass\n',
            'backend/src/database/math/migrations/add_x.py': 'DB = "--db"\n',
        }
        for path, text in files.items():
            target = self.repo/path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(text.encode())
        self.git('init', '-q', '-b', 'main')
        self.git('add', '-A')
        self.git('-c', 'user.name=t', '-c', 'user.email=t@example.com', 'commit', '-q', '-m', 'main')
        live = {
            'backend/src/app.py': 'print("app")\n',                       # same
            'backend/src/routes/math.py': 'ROUTE = 2  # edited on server\n',  # differs
            'frontend/index.html': '<p>home</p>\r\n',                     # line endings only
            'frontend/geography/places-data.js': 'window.PLACES = [1];\n',  # content
            'docs/README.md': 'old docs\n',                               # other
            'backend/src/hotfix.py': 'X = 1\n',                           # only on live
            'backend/src/database/math/migrations/add_x.py': 'DB = None\n',  # laptop script, not site code
            'manifest.json': '{}',                                        # first-deployment leftover
            'backend/portfolio.db': 'SQLite',                             # ignored, not hashed
            'backend/data/math/diagrams/a.svg': '<svg/>',                 # ignored
            'backend/src/__pycache__/app.cpython-313.pyc': 'x',           # pruned
        }
        for path, text in live.items():
            target = self.live/path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(text.encode())

    def git(self, *args):
        subprocess.run(['git', '-C', str(self.repo), *args], check=True)

    def test_classifies_every_file_and_writes_report(self):
        out, buckets = drift.check(self.repo, 'cwoo', 'main', self.out, fetch=False,
                                   reader=run_reader_locally(self.live))
        self.assertEqual(buckets['same'], ['backend/src/app.py'])
        self.assertEqual(buckets['line endings'], ['frontend/index.html'])
        self.assertEqual(buckets['differs'], ['backend/src/database/math/migrations/add_x.py',
                                              'backend/src/routes/math.py', 'docs/README.md',
                                              'frontend/geography/places-data.js'])
        self.assertEqual(buckets['only on live'], ['backend/src/hotfix.py', 'manifest.json'])
        self.assertEqual(buckets['only on live (ignored)'], ['backend/data/math/diagrams/a.svg', 'backend/portfolio.db'])
        self.assertIn('backend/src/new_feature.py', buckets['missing on live'])
        self.assertEqual(drift.needs_decision(buckets), ['backend/src/routes/math.py', 'backend/src/hotfix.py'])
        self.assertFalse(any('__pycache__' in p for paths in buckets.values() for p in paths))

        report = (out/'report.md').read_text(encoding='utf-8')
        self.assertIn('+ROUTE = 2  # edited on server', report)
        self.assertIn('-ROUTE = 1', report)
        self.assertEqual((out/'live'/'backend/src/routes/math.py').read_text(), 'ROUTE = 2  # edited on server\n')
        self.assertEqual((out/'live'/'backend/src/hotfix.py').read_text(), 'X = 1\n')
        self.assertFalse((out/'live'/'backend/src/app.py').exists())
        self.assertEqual(json.loads((out/'summary.json').read_text())['buckets'], buckets)

    def test_database_files_are_listed_but_not_read(self):
        listing = run_reader_locally(self.live)('cwoo', dict(
            root='', main={}, prune_names=[], prune_paths=[], text_suffixes=['.py'],
            file_limit=1000, total_limit=1000))
        self.assertNotIn('raw', listing['files']['backend/portfolio.db'])
        self.assertIn('raw', listing['files']['backend/src/app.py'])

    def test_rejects_odd_username(self):
        with self.assertRaises(ValueError):
            drift.check(self.repo, 'cwoo; rm', 'main', self.out, fetch=False, reader=None)


if __name__ == '__main__':
    unittest.main()
