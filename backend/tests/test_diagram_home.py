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

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from bring_changes_home import refresh
import diagram_home
from test_diagram_sync import SVG

A, B, C = 'a' * 16, 'b' * 16, 'c' * 16


def svg(label):
    return SVG.replace('dvisvgm 3.1.2', label).encode()


class DiagramHomeTests(unittest.TestCase):
    """Option 8 after a diagram publish: rows compared by content, SVGs brought home without overwriting."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.base, self.local, self.live = (self.root / n for n in ('base.db', 'working.db', 'live-snapshot.db'))
        self.diagrams = self.root / 'diagrams'
        self.diagrams.mkdir()
        self.server = {}  # name -> bytes on the "server"
        with closing(sqlite3.connect(self.base)) as db:
            db.executescript('''
                CREATE TABLE math_concepts(id INTEGER PRIMARY KEY, canonical_name TEXT, cleaned_tex TEXT,
                    rendered_tex TEXT, created_at TEXT, updated_at TEXT);
                CREATE TABLE math_synonyms(id INTEGER PRIMARY KEY AUTOINCREMENT, concept_id INTEGER, synonym_text TEXT);
                CREATE TABLE math_concept_diagrams(id INTEGER PRIMARY KEY AUTOINCREMENT, concept_id INTEGER, block_index INTEGER,
                    source_hash TEXT, source_tex TEXT, svg_path TEXT, created_at TEXT);
                CREATE TABLE math_concept_diagram_failures(id INTEGER PRIMARY KEY, concept_id INTEGER, source_hash TEXT);
                INSERT INTO math_concepts VALUES(1, 'RootedTree', 'tree', '<p>tree</p>', 't0', 't0');
                INSERT INTO math_concepts VALUES(2, 'Ball', 'ball', '<p>ball</p>', 't0', 't0');
                INSERT INTO math_synonyms(concept_id, synonym_text) VALUES(1, 'arborescence');
            ''')
            self.add_row(db, 2, A)
            db.commit()
        shutil.copyfile(self.base, self.local)
        shutil.copyfile(self.base, self.live)
        self.server[A + '.svg'] = svg('A')
        (self.diagrams / (A + '.svg')).write_bytes(svg('A'))
        self.state = dict(base=str(self.base), working=str(self.local), username='cwoo', job=None,
                          base_sha256=hashlib.sha256(self.base.read_bytes()).hexdigest())

    @staticmethod
    def add_row(db, concept, source_hash, created='2026-10-22 08:00:00'):
        db.execute('INSERT INTO math_concept_diagrams(concept_id, block_index, source_hash, source_tex, svg_path, created_at) '
                   'VALUES(?, 1, ?, ?, ?, ?)', (concept, source_hash, 'source ' + source_hash,
                                                '/api/math/diagrams/' + source_hash + '.svg', created))

    def publish(self, source_hash, data):
        """The same diagram stored locally (option 19) and on the live site (published later)."""
        for path, created in ((self.local, '2026-10-22 08:00:00'), (self.live, '2026-10-22 09:30:00')):
            with closing(sqlite3.connect(path)) as db:
                db.execute('INSERT INTO math_concept_diagrams(id, concept_id, block_index, source_hash, source_tex, svg_path, created_at) '
                           'VALUES(?, 1, 1, ?, ?, ?, ?)', (50 if path == self.live else 7, source_hash, 'source ' + source_hash,
                                                            '/api/math/diagrams/' + source_hash + '.svg', created))
                db.commit()
        self.server[source_hash + '.svg'] = data

    def manifest(self, username, names):
        return {n: ({'sha256': hashlib.sha256(self.server[n]).hexdigest(), 'size': len(self.server[n])}
                    if n in self.server else None) for n in names}

    def scp(self, command, check):
        name = command[1].rsplit('/', 1)[-1]
        Path(command[2]).write_bytes(self.served.get(name, self.server.get(name)))
        return subprocess.CompletedProcess(command, 0)

    def run_refresh(self, served=None):
        self.served = served or {}
        self.live.with_name('snapshot.json').write_text(json.dumps(dict(
            sha256=hashlib.sha256(self.live.read_bytes()).hexdigest(),
            source='/home/cwoo/chi-portfolio/backend/portfolio.db')))
        with patch.object(diagram_home, 'remote_manifest', side_effect=self.manifest), \
                patch.object(diagram_home.subprocess, 'run', side_effect=self.scp):
            return refresh(self.state, self.live, self.root / 'copies', Mock(), diagrams=self.diagrams)

    def test_published_diagram_refreshes_and_missing_svg_is_downloaded(self):
        self.publish(B, svg('B'))
        with closing(sqlite3.connect(self.local)) as db:
            db.execute("INSERT INTO math_concept_diagram_failures VALUES(1, 1, 'dead')")  # Local diagnostics only.
            db.commit()
        result = self.run_refresh()
        self.assertTrue(result['safe'], result)
        self.assertEqual((result['diagrams_verified'], result['diagrams_downloaded']), (1, 1))
        self.assertEqual((self.diagrams / (B + '.svg')).read_bytes(), svg('B'))
        self.assertEqual(sorted(p.name for p in self.diagrams.iterdir()), [A + '.svg', B + '.svg'])
        self.assertEqual(Path(self.state['working']).read_bytes(), self.live.read_bytes())

    def test_local_rendering_with_different_bytes_is_kept(self):
        self.publish(B, svg('server render'))
        (self.diagrams / (B + '.svg')).write_bytes(svg('laptop render'))
        result = self.run_refresh()
        self.assertTrue(result['safe'])
        self.assertEqual(result['diagrams_kept_local'], [B + '.svg'])
        self.assertEqual((self.diagrams / (B + '.svg')).read_bytes(), svg('laptop render'))

    def test_unusable_local_file_or_bad_download_stops_before_switching(self):
        self.publish(B, svg('B'))
        old_state = dict(self.state)
        (self.diagrams / (B + '.svg')).write_bytes(b'<svg broken')
        with self.assertRaisesRegex(ValueError, 'Remove it'):
            self.run_refresh()
        self.assertEqual(self.state, old_state)
        (self.diagrams / (B + '.svg')).unlink()
        with self.assertRaisesRegex(ValueError, 'Missing or different diagram file'):
            self.run_refresh(served={B + '.svg': svg('tampered')})
        self.assertEqual(self.state, old_state)
        self.assertFalse((self.diagrams / (B + '.svg')).exists())

    def test_server_missing_file_reported_not_blocking(self):
        self.publish(B, svg('B'))
        del self.server[B + '.svg']
        result = self.run_refresh()
        self.assertTrue(result['safe'])
        self.assertEqual(result['diagrams_missing_on_server'], [B + '.svg'])

    def test_unpublished_local_diagram_still_blocks(self):
        with closing(sqlite3.connect(self.local)) as db:
            self.add_row(db, 1, C)
            db.commit()
        result = self.run_refresh()
        self.assertFalse(result['safe'])
        self.assertEqual(result['blocked'], ['math_concept_diagrams'])

    def test_without_diagrams_folder_changed_rows_still_need_review(self):
        self.publish(B, svg('B'))
        self.live.with_name('snapshot.json').write_text(json.dumps(dict(
            sha256=hashlib.sha256(self.live.read_bytes()).hexdigest(),
            source='/home/cwoo/chi-portfolio/backend/portfolio.db')))
        result = refresh(self.state, self.live, self.root / 'copies', Mock())
        self.assertFalse(result['safe'])

    def test_manifest_script_reads_only_hash_named_files(self):
        home = self.root / 'home' / 'cwoo' / 'chi-portfolio' / 'backend' / 'data' / 'math' / 'diagrams'
        home.mkdir(parents=True)
        (home / (A + '.svg')).write_bytes(svg('A'))
        script = diagram_home.MANIFEST_SCRIPT.replace("'/home/'", repr(str(self.root / 'home') + '/'))
        run = lambda names: subprocess.run([sys.executable, '-I', '-B', '-c', script], text=True, capture_output=True,
                                           input=json.dumps(dict(username='cwoo', names=names)))
        result = run([A + '.svg', B + '.svg'])
        manifest = json.loads(result.stdout.split('DIAGRAM_MANIFEST=')[1])
        self.assertEqual(manifest, {A + '.svg': {'sha256': hashlib.sha256(svg('A')).hexdigest(), 'size': len(svg('A'))},
                                    B + '.svg': None})
        self.assertNotEqual(run(['../../portfolio.db']).returncode, 0)

    def edit_both(self, local_sql, live_sql):
        for path, sql in ((self.local, local_sql), (self.live, live_sql)):
            with closing(sqlite3.connect(path)) as db:
                db.executescript(sql)
                db.commit()

    def test_published_text_edit_matches_despite_timestamps_page_html_and_row_ids(self):
        self.edit_both("""UPDATE math_concepts SET cleaned_tex='tree, fixed', rendered_tex='<p>local</p>', updated_at='t1' WHERE id=1;
                          DELETE FROM math_synonyms; INSERT INTO math_synonyms(concept_id, synonym_text) VALUES(1, 'out-tree');""",
                       """INSERT INTO math_synonyms(concept_id, synonym_text) VALUES(2, 'scratch'); DELETE FROM math_synonyms WHERE synonym_text='scratch';
                          UPDATE math_concepts SET cleaned_tex='tree, fixed', rendered_tex='<p>server</p>', updated_at='t2' WHERE id=1;
                          DELETE FROM math_synonyms; INSERT INTO math_synonyms(concept_id, synonym_text) VALUES(1, 'out-tree');""")
        result = self.run_refresh()
        self.assertTrue(result['safe'], result)

    def test_unpublished_local_text_edit_still_blocks(self):
        self.edit_both("UPDATE math_concepts SET cleaned_tex='tree, draft' WHERE id=1;", "SELECT 1;")
        result = self.run_refresh()
        self.assertFalse(result['safe'])
        self.assertEqual(result['blocked'], ['math_concepts'])


if __name__ == '__main__':
    unittest.main()
