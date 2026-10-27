from contextlib import closing
from datetime import datetime, timedelta, timezone
import gzip
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from database import nightly_backup as nb

START = datetime(2026, 10, 27, 10, 17, tzinfo=timezone.utc)


def make_db(path, entries=3):
    with closing(sqlite3.connect(path)) as db:
        db.execute('CREATE TABLE math_concepts(id INTEGER PRIMARY KEY, title TEXT)')
        db.executemany('INSERT INTO math_concepts(title) VALUES (?)', [(f'entry {i}',) for i in range(entries)])
        db.commit()


def count(path):
    with closing(sqlite3.connect(path)) as db:
        return db.execute('SELECT COUNT(*) FROM math_concepts').fetchone()[0]


class NightlyBackupTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.live = self.root / 'portfolio.db'
        self.folder = self.root / 'backups' / 'nightly'
        make_db(self.live)

    def test_backup_is_verified_compressed_copy_with_note(self):
        report = nb.backup(self.live, self.folder, now=START)
        final = Path(report['backup'])
        self.assertEqual(final.name, 'portfolio-20261027T101700Z.db.gz')
        note = json.loads(final.with_name('portfolio-20261027T101700Z.json').read_text())
        self.assertEqual(note['integrity'], 'ok')
        self.assertEqual(note['math_concepts'], 3)
        restored = self.root / 'restored.db'
        restored.write_bytes(gzip.decompress(final.read_bytes()))
        self.assertEqual(count(restored), 3)
        # No temporary files are left behind.
        self.assertEqual(sorted(p.name for p in self.folder.iterdir()),
                         ['portfolio-20261027T101700Z.db.gz', 'portfolio-20261027T101700Z.json'])

    def test_backup_while_another_connection_holds_a_write_transaction(self):
        with closing(sqlite3.connect(self.live)) as writer:
            writer.execute('BEGIN IMMEDIATE')
            writer.execute("INSERT INTO math_concepts(title) VALUES ('uncommitted')")
            report = nb.backup(self.live, self.folder, now=START)
            writer.rollback()
        # The snapshot holds the last committed state only.
        self.assertEqual(report['math_concepts'], 3)

    def test_backup_refuses_a_file_that_is_not_the_portfolio_database(self):
        other = self.root / 'other.db'
        with closing(sqlite3.connect(other)) as db:
            db.execute('CREATE TABLE t(x)')
            db.commit()
        with self.assertRaises(RuntimeError):
            nb.backup(other, self.folder, now=START)
        self.assertEqual(list(self.folder.iterdir()), [])

    def test_missing_database_raises_and_makes_nothing(self):
        with self.assertRaises(FileNotFoundError):
            nb.backup(self.root / 'missing.db', self.folder, now=START)
        self.assertFalse(self.folder.exists())

    def test_failed_verification_keeps_nothing_and_deletes_nothing(self):
        for day in range(10):
            nb.backup(self.live, self.folder, now=START - timedelta(days=10 - day))
        before = sorted(p.name for p in self.folder.iterdir())
        original = nb._gunzip_sha256
        nb._gunzip_sha256 = lambda path: ('0' * 64, 0)
        try:
            with self.assertRaises(RuntimeError):
                nb.backup(self.live, self.folder, now=START)
        finally:
            nb._gunzip_sha256 = original
        self.assertEqual(sorted(p.name for p in self.folder.iterdir()), before)

    def test_same_second_backup_never_overwrites(self):
        nb.backup(self.live, self.folder, now=START)
        with self.assertRaises(FileExistsError):
            nb.backup(self.live, self.folder, now=START)

    def test_retention_keeps_daily_weekly_and_monthly(self):
        stamps = [START - timedelta(days=d) for d in range(400)]
        keep = nb.to_keep(stamps)
        days = sorted({s.date() for s in keep}, reverse=True)
        # The last seven days are all kept.
        self.assertEqual(days[:7], [(START - timedelta(days=d)).date() for d in range(7)])
        months = {(s.year, s.month) for s in keep}
        self.assertEqual(len(months), 6)
        self.assertLessEqual(len(keep), 7 + 4 + 6)
        self.assertIn(max(stamps), keep)

    def test_rotation_deletes_only_nightly_files(self):
        for day in range(40):
            nb.backup(self.live, self.folder, now=START - timedelta(days=40 - day))
        for name in ('before-restore-x.db', 'portfolio-notes.txt', 'portfolio-20200101T000000Z.db'):
            (self.folder / name).write_text('keep me')
        report = nb.backup(self.live, self.folder, now=START)
        self.assertTrue(report['deleted'])
        for name in ('before-restore-x.db', 'portfolio-notes.txt', 'portfolio-20200101T000000Z.db'):
            self.assertTrue((self.folder / name).exists(), name)
        kept = nb.nightly_backups(self.folder)
        self.assertEqual(report['kept'], len(kept))
        self.assertLessEqual(len(kept), 7 + 4 + 6)
        # Each kept backup still has its note; deleted ones lost theirs too.
        notes = {p.name[:-len('.json')] for p in self.folder.glob('portfolio-*.json')}
        self.assertEqual(notes, {p.name[:-len('.db.gz')] for _, p in kept})

    def test_stale_partial_files_are_cleaned_up(self):
        self.folder.mkdir(parents=True)
        stale = self.folder / '.portfolio-20261020T000000Z-abcd.db.partial'
        fresh = self.folder / '.portfolio-20261027T100000Z-abcd.db.partial'
        stale.write_text('x')
        fresh.write_text('x')
        old = START.timestamp() - 3 * 86400
        os.utime(stale, (old, old))
        os.utime(fresh, (START.timestamp(), START.timestamp()))
        nb.backup(self.live, self.folder, now=START)
        self.assertFalse(stale.exists())
        self.assertTrue(fresh.exists())

    def test_size_warning(self):
        report = nb.backup(self.live, self.folder, now=START, warn_mb=0)
        self.assertIn('warning', report)

    def test_check_and_extract_detect_damage(self):
        good = Path(nb.backup(self.live, self.folder, now=START - timedelta(days=1))['backup'])
        bad = Path(nb.backup(self.live, self.folder, now=START)['backup'])
        make_db(self.root / 'changed.db', entries=5)
        bad.write_bytes(gzip.compress((self.root / 'changed.db').read_bytes()))
        rows = nb.check_all(self.folder)
        self.assertEqual([(name, ok) for name, ok, _ in rows], [(bad.name, False), (good.name, True)])
        with self.assertRaises(RuntimeError):
            nb.extract(bad, self.root / 'x.db')
        self.assertFalse((self.root / 'x.db').exists())
        self.assertEqual(nb.extract(good, self.root / 'y.db')['math_concepts'], 3)
        with self.assertRaises(FileExistsError):
            nb.extract(good, self.root / 'y.db')
        self.assertEqual(sorted(p.name for p in self.root.iterdir() if p.name.startswith('.')), [])

    def test_restore_live_previews_then_restores_with_safety_copy(self):
        saved = Path(nb.backup(self.live, self.folder, now=START)['backup'])
        with closing(sqlite3.connect(self.live)) as db:
            db.execute("INSERT INTO math_concepts(title) VALUES ('bad edit')")
            db.commit()
        preview = nb.restore_live(saved, self.live, self.folder.parent)
        self.assertEqual((preview['status'], preview['live_math_concepts'], preview['backup_math_concepts']),
                         ('preview', 4, 3))
        self.assertEqual(count(self.live), 4)
        # A reader stays connected, as the website would be.
        with closing(sqlite3.connect(self.live)) as reader:
            report = nb.restore_live(saved, self.live, self.folder.parent, apply=True)
            self.assertEqual(reader.execute('SELECT COUNT(*) FROM math_concepts').fetchone()[0], 3)
        self.assertEqual(report['status'], 'restored')
        self.assertEqual(count(self.live), 3)
        self.assertEqual(count(report['before_restore_copy']), 4)
        # The safety copy's name is outside the rotation pattern.
        self.assertIsNone(nb.stamp_of(report['before_restore_copy']))

    def test_command_line(self):
        out = self.root / 'out.db'
        with open(os.devnull, 'w') as quiet:
            stdout, sys.stdout = sys.stdout, quiet
            try:
                self.assertEqual(nb.main(['backup', '--database', str(self.live), '--backups', str(self.folder)]), 0)
                self.assertEqual(nb.main(['check', '--backups', str(self.folder)]), 0)
                saved = nb.nightly_backups(self.folder)[0][1]
                self.assertEqual(nb.main(['extract', str(saved), '--output', str(out)]), 0)
                self.assertEqual(nb.main(['restore-live', str(saved), '--database', str(self.live),
                                          '--backups', str(self.folder.parent)]), 0)
                with self.assertRaises(SystemExit):
                    nb.main(['backup', '--database', str(self.live)])
            finally:
                sys.stdout = stdout
        self.assertEqual(count(out), 3)
        self.assertEqual(list(self.folder.parent.glob('before-restore-*')), [])


if __name__ == '__main__':
    unittest.main()
