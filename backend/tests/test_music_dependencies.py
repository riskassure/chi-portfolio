"""Keep current top-track refresh usable without the historical export modules."""
from pathlib import Path
import subprocess
import sys
import unittest


class MusicDependencyTests(unittest.TestCase):
    def test_current_refresh_and_queries_without_history_modules(self):
        backend = Path(__file__).resolve().parents[1]
        script = '''
import sys, unittest
sys.path[:0] = ['src', 'tests']
for name in ('spotify_history', 'history_publication', 'spotify_sync',
             'spotify_downloads', 'spotify_jobs'):
    sys.modules['services.music.' + name] = None
suite = unittest.defaultTestLoader.loadTestsFromName('test_spotify_top')
result = unittest.TextTestRunner().run(suite)
raise SystemExit(not result.wasSuccessful())
'''
        result = subprocess.run([sys.executable, '-B', '-c', script], cwd=backend,
                                capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
