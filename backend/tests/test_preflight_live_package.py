import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from preflight_live_package import BOOTSTRAP, build_request, preflight


class LivePreflightTests(unittest.TestCase):
    def test_remote_checker_read_only_and_duplicate(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            database = root / 'live.db'
            db = sqlite3.connect(database)
            db.executescript('''
                CREATE TABLE math_concepts(id INTEGER PRIMARY KEY,canonical_name TEXT,slug TEXT,title TEXT,owner TEXT,cleaned_tex TEXT,is_cleaned INTEGER);
                CREATE TABLE math_classifications(id INTEGER PRIMARY KEY,code TEXT);
                CREATE TABLE math_types(id INTEGER PRIMARY KEY,type_name TEXT);
                CREATE TABLE math_concept_classifications(concept_id INTEGER,classification_id INTEGER);
                CREATE TABLE math_concept_types(concept_id INTEGER,type_id INTEGER);
                CREATE TABLE math_synonyms(concept_id INTEGER,synonym_text TEXT);
                CREATE TABLE math_definitions(concept_id INTEGER,defined_term TEXT);
                CREATE TABLE math_link_exclusions(concept_id INTEGER,word TEXT);
                CREATE TABLE math_related_concepts(concept_id INTEGER,related_canonical_name TEXT);
                INSERT INTO math_classifications VALUES(10,'54E35');
                INSERT INTO math_types VALUES(20,'Definition');
            ''')
            entry = dict(canonical_name='Test', slug='test', title='Test', owner='CWoo',
                         cleaned_tex='Definition.', is_cleaned=1, classifications=['54E35'],
                         types=['Definition'], synonyms=[], definitions=[], link_exclusions=[], related_concepts=[])
            package = root / 'package.zip'
            with zipfile.ZipFile(package, 'w') as archive:
                archive.writestr('entry.json', json.dumps(entry))
                archive.writestr('malicious.py', 'raise RuntimeError("Must never run")')
            request = build_request('cwoo', '/home/cwoo/chi-portfolio-staging/' + 'a'*32 + '/package.zip', package)
            request.update(remote=str(package), database=str(database))

            def run_check():
                before = hashlib.sha256(database.read_bytes()).digest()
                result = subprocess.run([sys.executable, '-I', '-B', '-c', BOOTSTRAP],
                                        input=json.dumps(request), capture_output=True, text=True, encoding='utf-8')
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(before, hashlib.sha256(database.read_bytes()).digest())
                return json.loads(result.stdout.split('PREFLIGHT_RESULT=')[1])['report']

            self.assertIn('NO DUPLICATE FOUND', run_check())
            db.execute('INSERT INTO math_concepts VALUES(1,?,?,?,?,?,?)',
                       tuple(entry[k] for k in ('canonical_name','slug','title','owner','cleaned_tex','is_cleaned')))
            db.execute('INSERT INTO math_concept_classifications VALUES(1,10)')
            db.execute('INSERT INTO math_concept_types VALUES(1,20)')
            db.commit()
            self.assertIn('ALREADY PRESENT', run_check())
            db.execute("UPDATE math_concepts SET cleaned_tex='New live edit'")
            db.commit()
            self.assertIn('BLOCKED', run_check())
            db.close()
            request['sha256'] = '0'*64
            result = subprocess.run([sys.executable, '-I', '-B', '-c', BOOTSTRAP],
                                    input=json.dumps(request), capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn('PREFLIGHT_RESULT=', result.stdout)

    def test_existing_report_and_unsafe_paths_fail_before_ssh(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / 'report.txt'
            output.write_text('Keep this report')
            with patch('preflight_live_package.subprocess.run') as run:
                with self.assertRaises(ValueError):
                    preflight('cwoo', 'remote', Path('missing.zip'), output)
                with self.assertRaises(ValueError):
                    build_request('cwoo', '/home/cwoo/chi-portfolio/backend/portfolio.db', Path('missing.zip'))
                run.assert_not_called()
            self.assertEqual(output.read_text(), 'Keep this report')
