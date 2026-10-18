"""Verify explicit setup and retained utilities on isolated directory trees."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SRC = Path(__file__).resolve().parents[1] / 'src'
sys.path.insert(0, str(SRC))


class ConfigSetupTests(unittest.TestCase):
    def test_import_is_quiet_and_does_not_create_folders(self):
        with patch.object(Path, 'mkdir', side_effect=AssertionError('Import wrote a directory')):
            with redirect_stdout(io.StringIO()) as output:
                runpy.run_path(str(SRC / 'config.py'), run_name='isolated_config')
        self.assertEqual(output.getvalue(), '')

    def test_explicit_setup_in_fresh_tree_is_repeatable(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config = root / 'backend/src/config.py'
            config.parent.mkdir(parents=True)
            config.write_bytes((SRC / 'config.py').read_bytes())
            import os
            with patch.dict(os.environ, {}, clear=True), redirect_stdout(io.StringIO()):
                runpy.run_path(str(config), run_name='__main__')
                runpy.run_path(str(config), run_name='__main__')
            self.assertTrue((root / 'backend/data/music/processed').is_dir())
            self.assertTrue((root / 'frontend/images/photography').is_dir())
            self.assertTrue((root / 'backend/data/math/temp').is_dir())
            self.assertFalse(list(root.rglob('*.db')))

    def test_utilities_handle_missing_inputs_and_create_outputs(self):
        from utils import parse_playlist, convert_photos
        with tempfile.TemporaryDirectory() as temp, redirect_stdout(io.StringIO()):
            root = Path(temp)
            raw, output = root / 'raw', root / 'processed'
            with patch.object(parse_playlist, 'MUSIC_RAW_DIR', raw), patch.object(parse_playlist, 'MUSIC_PROCESSED_DIR', output):
                parse_playlist.run_pipeline()
                self.assertFalse(output.exists())
                raw.mkdir()
                (raw / 'favorites.csv').write_text('Track Name,Popularity\nQuiet,5\nFavorite,90\n')
                parse_playlist.run_pipeline(top_n_tracks=1)
                tracks = json.loads((output / 'all_playlists.json').read_text())
                self.assertEqual(tracks[0]['Track Name'], 'Favorite')
                self.assertEqual(len(tracks), 1)
            with patch.object(convert_photos, 'PHOTO_RAW_DIR', root / 'missing-photos'), patch.object(convert_photos, 'PHOTO_TARGET_DIR', root / 'photos'):
                convert_photos.batch_convert_to_webp()
                self.assertEqual(list((root / 'photos').iterdir()), [])

    def test_web_startup_does_not_create_data_directories(self):
        script = '''
from pathlib import Path
from unittest.mock import patch
with patch.object(Path, 'mkdir', side_effect=AssertionError('Startup created data folders')):
    import app
    assert app.app.test_client().get('/api/session-check').status_code == 200
'''
        result = subprocess.run([sys.executable, '-B', '-c', script], cwd=SRC, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
