from contextlib import closing
import hashlib
import io
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from live_math_publication import publish
from publish_staged_package import publish_staged


class PublicationTests(unittest.TestCase):
    def package(self, payload):
        data = io.BytesIO()
        with zipfile.ZipFile(data, 'w') as archive:
            archive.writestr('entry.json', json.dumps(payload))
            archive.writestr('untrusted.py', 'raise RuntimeError("Do not execute")')
        return data.getvalue()

    def test_apply_repeat_conflict_and_text_patch(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            database = root / 'live.db'
            db = sqlite3.connect(database)
            db.executescript('''
                CREATE TABLE math_concepts(id INTEGER PRIMARY KEY,canonical_name TEXT,slug TEXT,title TEXT,owner TEXT,cleaned_tex TEXT,is_cleaned INTEGER,rendered_tex TEXT,created_at TEXT,updated_at TEXT);
                CREATE TABLE math_classifications(id INTEGER PRIMARY KEY,code TEXT);
                CREATE TABLE math_types(id INTEGER PRIMARY KEY,type_name TEXT);
                CREATE TABLE math_concept_classifications(concept_id INTEGER,classification_id INTEGER);
                CREATE TABLE math_concept_types(concept_id INTEGER,type_id INTEGER);
                CREATE TABLE math_synonyms(concept_id INTEGER,synonym_text TEXT);
                CREATE TABLE math_definitions(concept_id INTEGER,defined_term TEXT);
                CREATE TABLE math_link_exclusions(concept_id INTEGER,word TEXT);
                CREATE TABLE math_related_concepts(concept_id INTEGER,related_canonical_name TEXT,related_concept_id INTEGER);
                INSERT INTO math_classifications VALUES(10,'54E35');
                INSERT INTO math_types VALUES(20,'Definition');
            ''')
            db.close()
            entry = dict(canonical_name='Test', slug='test', title='Test', owner='CWoo',
                         cleaned_tex='Definition.', is_cleaned=1, classifications=['54E35'],
                         types=['Definition'], synonyms=[], definitions=[], link_exclusions=[], related_concepts=[])
            backups = root / 'backups'
            source = Path(__file__).resolve().parents[1] / 'src'
            data = self.package(entry)
            result = publish(data, database, backups, source)
            self.assertEqual(result['status'], 'APPLIED')
            self.assertTrue(Path(result['backup']).is_file())
            before = database.read_bytes()
            self.assertEqual(publish(data, database, backups, source)['status'], 'ALREADY_PRESENT')
            self.assertEqual(before, database.read_bytes())
            self.assertEqual(len(list(backups.iterdir())), 1)
            with self.assertRaises(ValueError):
                publish(self.package(dict(entry, cleaned_tex='Conflicting addition')), database, backups, source)
            self.assertEqual(before, database.read_bytes())
            expected = {k: v for k, v in entry.items() if k != 'canonical_name'}
            payload = dict(canonical_name='Test', expected=expected, replacement_tex='Revised definition.',
                           replacement_synonyms=['new alias'])
            # An alias insertion failure must roll back the content update too.
            with closing(sqlite3.connect(database)) as connection:
                connection.execute("CREATE TRIGGER reject_alias BEFORE INSERT ON math_synonyms BEGIN SELECT RAISE(ABORT, 'test failure'); END")
            with patch('services.math.concept_render_service.render_tex_reusing_existing_diagrams', return_value='<p>Revised definition.</p>'):
                with self.assertRaises(sqlite3.IntegrityError):
                    publish(self.package(payload), database, backups, source)
            with closing(sqlite3.connect(database)) as connection:
                self.assertEqual(connection.execute('SELECT cleaned_tex FROM math_concepts').fetchone()[0], 'Definition.')
                self.assertEqual(connection.execute('SELECT COUNT(*) FROM math_synonyms').fetchone()[0], 0)
                connection.execute('DROP TRIGGER reject_alias')
            # Exercise real transaction/backup/update while avoiding unrelated diagram schema.
            with patch('services.math.concept_render_service.render_tex_reusing_existing_diagrams', return_value='<p>Revised definition.</p>'):
                self.assertEqual(publish(self.package(payload), database, backups, source)['status'], 'APPLIED')
            self.assertEqual(publish(self.package(payload), database, backups, source)['status'], 'ALREADY_PRESENT')
            with closing(sqlite3.connect(database)) as connection:
                self.assertEqual(connection.execute('SELECT synonym_text FROM math_synonyms').fetchone()[0], 'new alias')
            with self.assertRaisesRegex(ValueError, 'Conflict'):
                publish(self.package(dict(payload, replacement_tex='Stale revision')), database, backups, source)
            self.assertEqual(len(list(backups.iterdir())), 3)

    def test_lost_connection_keeps_pending_receipt(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            package = root / 'package.zip'
            package.write_bytes(self.package({'test': 'payload'}))
            output = root / 'receipt.json'
            remote = '/home/cwoo/chi-portfolio-staging/' + 'a'*32 + '/package.zip'
            with patch('publish_staged_package.shutil.which', return_value='ssh'), \
                 patch('publish_staged_package.subprocess.run', side_effect=OSError('connection lost')):
                with self.assertRaisesRegex(RuntimeError, 'unconfirmed'):
                    publish_staged('cwoo', remote, package, output)
            receipt = json.loads(output.read_text())
            self.assertEqual(receipt['status'], 'PENDING')
            self.assertEqual(receipt['sha256'], hashlib.sha256(package.read_bytes()).hexdigest())
