from contextlib import closing, redirect_stdout, redirect_stderr
import argparse
import hashlib
import io
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

BACKEND = Path(__file__).resolve().parents[1]
MIGRATIONS = BACKEND / 'src' / 'database' / 'math' / 'migrations'
sys.path.insert(0, str(BACKEND / 'src'))
sys.path.insert(0, str(MIGRATIONS))
import add_autolink_inflection_synonyms
import migration_db

SCRIPTS = sorted(p for p in MIGRATIONS.glob('*.py') if p.name not in {'__init__.py', 'migration_db.py', 'math_entry_batch.py'})

SCHEMA = '''
CREATE TABLE math_concepts (id INTEGER PRIMARY KEY, slug TEXT UNIQUE, canonical_name TEXT,
    title TEXT, cleaned_tex TEXT, rendered_tex TEXT, updated_at TEXT);
CREATE TABLE math_synonyms (id INTEGER PRIMARY KEY, concept_id INTEGER, synonym_text TEXT);
CREATE TABLE math_related_concepts (id INTEGER PRIMARY KEY, concept_id INTEGER,
    related_canonical_name TEXT, related_concept_id INTEGER);
CREATE TABLE music_publication (id INTEGER PRIMARY KEY, note TEXT);
'''


def make_catalog(path, slugs=('alpha', 'beta')):
    with closing(sqlite3.connect(path)) as c:
        c.executescript(SCHEMA)
        c.executemany('INSERT INTO math_concepts(slug,canonical_name,title,cleaned_tex) VALUES (?,?,?,?)',
                      [(s, s.title(), s, 'Text about ' + s) for s in slugs])
        c.commit()
    return path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(script, *args, cwd):
    return subprocess.run([sys.executable, str(script), *args], cwd=cwd,
                          capture_output=True, text=True, timeout=120)


class ScriptCommandLineTests(unittest.TestCase):
    def setUp(self):
        self.folder = Path(tempfile.mkdtemp())
        self.legacy = BACKEND / 'portfolio.db'
        self.legacy_existed = self.legacy.exists()
        self.legacy_digest = digest(self.legacy) if self.legacy_existed else None

    def tearDown(self):
        # No script may fall back to the old default database.
        self.assertEqual(self.legacy.exists(), self.legacy_existed)
        if self.legacy_existed:
            self.assertEqual(digest(self.legacy), self.legacy_digest)

    def test_every_script_requires_db(self):
        self.assertEqual(len(SCRIPTS), 39)
        for script in SCRIPTS:
            with self.subTest(script=script.name):
                result = run(script, cwd=self.folder)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn('--db', result.stderr)

    def test_every_script_refuses_a_missing_database_without_creating_it(self):
        missing = self.folder / 'typo.db'
        for script in SCRIPTS:
            with self.subTest(script=script.name):
                result = run(script, '--db', str(missing), cwd=self.folder)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn('no database file', result.stderr)
                self.assertFalse(missing.exists())

    def test_autolink_script_previews_by_default(self):
        db = make_catalog(self.folder / 'working.db', add_autolink_inflection_synonyms.INFLECTION_SYNONYMS)
        before = digest(db)
        result = run(MIGRATIONS / 'add_autolink_inflection_synonyms.py', '--db', str(db), cwd=self.folder)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(digest(db), before)
        self.assertFalse((self.folder / 'backups').exists())
        self.assertIn('PREVIEW ONLY', result.stdout)
        self.assertIn('  angle: synonyms +1', result.stdout)
        self.assertIn('New entries (0): none', result.stdout)

    def test_autolink_script_backs_up_before_applying(self):
        db = make_catalog(self.folder / 'working.db', add_autolink_inflection_synonyms.INFLECTION_SYNONYMS)
        result = run(MIGRATIONS / 'add_autolink_inflection_synonyms.py', '--db', str(db), '--apply',
                     cwd=self.folder)
        self.assertEqual(result.returncode, 0, result.stderr)
        backups = list((self.folder / 'backups').glob('working.before-add_autolink_inflection_synonyms-*.db'))
        self.assertEqual(len(backups), 1)
        self.assertIn(f'Backup: {backups[0]}', result.stdout)
        with closing(sqlite3.connect(backups[0])) as c:
            self.assertEqual(c.execute('SELECT count(*) FROM math_synonyms').fetchone()[0], 0)
        with closing(sqlite3.connect(db)) as c:
            count = c.execute('SELECT count(*) FROM math_synonyms').fetchone()[0]
        self.assertEqual(count, len(add_autolink_inflection_synonyms.INFLECTION_SYNONYMS))

    def test_compare_lists_changes_since_a_backup(self):
        backup = make_catalog(self.folder / 'backup.db')
        db = self.folder / 'working.db'
        db.write_bytes(backup.read_bytes())
        with closing(sqlite3.connect(db)) as c:
            c.execute("UPDATE math_concepts SET title='renamed' WHERE slug='beta'")
            c.commit()
        result = run(MIGRATIONS / 'migration_db.py', str(backup), str(db), cwd=self.folder)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('  beta: title', result.stdout)

    def test_backfill_requires_db(self):
        result = run(MIGRATIONS / 'backfill_local_macro_preludes.py', cwd=self.folder)
        self.assertEqual(result.returncode, 2)
        self.assertIn('--db', result.stderr)


class DatabaseArgumentTests(unittest.TestCase):
    def setUp(self):
        self.folder = Path(tempfile.mkdtemp())

    def test_rejects_files_that_are_not_the_catalog(self):
        text = self.folder / 'notes.db'
        text.write_text('not a database')
        empty = self.folder / 'empty.db'
        sqlite3.connect(empty).close()
        for path, message in [(text, 'not a readable SQLite database'), (empty, 'no math_concepts table')]:
            with self.subTest(path=path.name), self.assertRaisesRegex(argparse.ArgumentTypeError, message):
                migration_db.existing_database(str(path))

    def target(self, db, *extra, change=None, fail=False):
        output = io.StringIO()
        with redirect_stdout(output), redirect_stderr(output):
            try:
                with migration_db.migration_target(argparse.ArgumentParser(), ['--db', str(db), *extra]) as path:
                    with closing(sqlite3.connect(path)) as c:
                        (change or (lambda c: None))(c)
                        c.commit()
                    if fail:
                        raise RuntimeError('verification failed')
            except RuntimeError:
                pass
        return output.getvalue()

    def test_failed_preview_leaves_database_alone(self):
        db = make_catalog(self.folder / 'working.db')
        before = digest(db)
        out = self.target(db, change=lambda c: c.execute("DELETE FROM math_concepts"), fail=True)
        self.assertEqual(digest(db), before)
        self.assertIn('Nothing was written', out)

    def test_failed_apply_points_to_backup(self):
        db = make_catalog(self.folder / 'working.db')
        out = self.target(db, '--apply', change=lambda c: c.execute("UPDATE math_concepts SET title='x'"),
                          fail=True)
        backup = next((self.folder / 'backups').iterdir())
        self.assertIn(f'Backup taken before the run: {backup}', out)
        self.assertIn('stop everything that writes to the database', out)
        with closing(sqlite3.connect(backup)) as c:
            self.assertEqual(c.execute("SELECT title FROM math_concepts WHERE slug='alpha'").fetchone()[0], 'alpha')

    def test_preview_ignores_edits_made_by_another_writer(self):
        db = make_catalog(self.folder / 'working.db')

        def other_writer(_copy):
            # The migration itself does nothing; meanwhile the real database changes.
            with closing(sqlite3.connect(db)) as c:
                c.execute("UPDATE math_concepts SET title='renamed' WHERE slug='alpha'")
                c.commit()

        out = self.target(db, change=other_writer)
        self.assertIn('New entries (0): none', out)
        self.assertIn('Existing entries changed (0): none', out)
        self.assertNotIn('alpha', out)

    def test_preview_reports_changes_to_existing_entries(self):
        db = make_catalog(self.folder / 'working.db', ('alpha', 'beta', 'gamma'))

        def change(c):
            c.execute("INSERT INTO math_concepts(slug,canonical_name,title,cleaned_tex) VALUES ('delta','Delta','delta','new')")
            new_id = c.execute("SELECT id FROM math_concepts WHERE slug='delta'").fetchone()[0]
            c.execute("INSERT INTO math_synonyms(concept_id,synonym_text) VALUES (?, 'deltas')", (new_id,))
            c.execute("UPDATE math_concepts SET cleaned_tex='edited', rendered_tex='<p>edited</p>', updated_at='now' WHERE slug='alpha'")
            c.execute("UPDATE math_concepts SET rendered_tex='<p>re-rendered</p>' WHERE slug='gamma'")
            c.execute("INSERT INTO math_related_concepts(concept_id,related_canonical_name,related_concept_id) "
                      "SELECT id,'Delta',? FROM math_concepts WHERE slug='beta'", (new_id,))
            c.execute("INSERT INTO music_publication(note) VALUES ('x')")

        out = self.target(db, change=change)
        self.assertIn('New entries (1): delta', out)
        self.assertIn('Existing entries changed (3):', out)
        self.assertIn('  alpha: text\n', out)
        self.assertIn('  beta: related links +1\n', out)
        self.assertIn('  gamma: rendered_tex\n', out)
        self.assertIn('Other tables: music_publication +1', out)
        self.assertNotIn('deltas', out)


if __name__ == '__main__':
    unittest.main()
