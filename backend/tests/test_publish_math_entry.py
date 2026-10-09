from contextlib import closing
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from publish_math_entry import apply, validate


class NewEntryTests(unittest.TestCase):
    def test_insert_metadata_backup_and_duplicate(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); database=root/'test.db'
            with closing(sqlite3.connect(database)) as db:
                db.executescript('''
                CREATE TABLE math_concepts(id INTEGER PRIMARY KEY,canonical_name TEXT UNIQUE,slug TEXT,title TEXT,owner TEXT,cleaned_tex TEXT,is_cleaned INTEGER,rendered_tex TEXT,created_at TEXT,updated_at TEXT);
                CREATE TABLE math_classifications(id INTEGER PRIMARY KEY,code TEXT);
                CREATE TABLE math_types(id INTEGER PRIMARY KEY,type_name TEXT);
                CREATE TABLE math_concept_classifications(concept_id INTEGER,classification_id INTEGER);
                CREATE TABLE math_concept_types(concept_id INTEGER,type_id INTEGER);
                CREATE TABLE math_synonyms(concept_id INTEGER,synonym_text TEXT);
                CREATE TABLE math_definitions(concept_id INTEGER,defined_term TEXT);
                CREATE TABLE math_link_exclusions(concept_id INTEGER,word TEXT);
                CREATE TABLE math_related_concepts(concept_id INTEGER,related_canonical_name TEXT,related_concept_id INTEGER);
                INSERT INTO math_classifications VALUES(500,'20A05');
                INSERT INTO math_types VALUES(700,'Definition');
                ''')
                db.commit()
            entry=dict(canonical_name='SyncTest',slug='sync-test',title='Sync test',owner='CWoo',cleaned_tex='A test with $x=1$.',is_cleaned=1,classifications=['20A05'],types=['Definition'],synonyms=['test alias'],definitions=[],link_exclusions=['test'],related_concepts=[])
            source=Path(__file__).resolve().parents[1]/'src'
            bad=dict(entry,types=['Missing'])
            with self.assertRaises(ValueError): apply(database,bad,root/'backups',source)
            self.assertFalse((root/'backups').exists())
            backup=apply(database,entry,root/'backups',source)
            with closing(sqlite3.connect(backup)) as db:
                self.assertEqual(db.execute('SELECT COUNT(*) FROM math_concepts').fetchone()[0],0)
            with closing(sqlite3.connect(database)) as db:
                self.assertEqual(db.execute('SELECT classification_id FROM math_concept_classifications').fetchone()[0],500)
                self.assertTrue(db.execute('SELECT rendered_tex FROM math_concepts').fetchone()[0])
            with self.assertRaises(ValueError): apply(database,entry,root/'backups',source)
            with self.assertRaises(ValueError): validate(dict(entry,cleaned_tex=r'\includegraphics{photo.png}'))
