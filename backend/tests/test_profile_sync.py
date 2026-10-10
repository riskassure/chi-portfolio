from contextlib import closing
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import profile_sync as profile


class ProfileSyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.frontend = self.root/'frontend'
        self.frontend.mkdir()
        for page in ('bio','resume'):
            (self.frontend/(page+'.html')).write_text('<span data-page-text="name">Name</span>')
        self.db = self.root/'live.db'
        with closing(sqlite3.connect(self.db)) as db:
            db.execute('CREATE TABLE profile_page_revisions(page TEXT, revision INTEGER, content TEXT, saved_at TEXT DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(page,revision))')
            db.execute('INSERT INTO profile_page_revisions(page,revision,content) VALUES(?,?,?)', ('bio',1,json.dumps({'name':'Chi'})))
            db.commit()
        self.payload = dict(kind='profile', page='bio', expected=profile.page_state(self.db,'bio'),
                            replacement={'name':'Chi Woo'}, template_sha256=profile.template_info(self.frontend,'bio')[0])

    def test_apply_backup_and_repeat(self):
        result = profile.apply(self.db, self.payload, self.root/'backups', self.frontend)
        self.assertEqual(result['status'], 'APPLIED')
        self.assertEqual(profile.page_state(Path(result['backup']), 'bio')['fields'], {'name':'Chi'})
        self.assertEqual(profile.page_state(self.db,'bio'), {'version':2,'fields':{'name':'Chi Woo'}})
        self.assertEqual(profile.apply(self.db,self.payload,self.root/'backups',self.frontend)['status'],'ALREADY_PRESENT')
        self.assertEqual(len(list((self.root/'backups').iterdir())),1)

    def test_new_live_revision_blocks_even_if_text_reverted(self):
        with closing(sqlite3.connect(self.db)) as db:
            db.execute('INSERT INTO profile_page_revisions(page,revision,content) VALUES(?,?,?)',('bio',2,json.dumps({'name':'Chi'})))
            db.commit()
        with self.assertRaisesRegex(ValueError,'CONFLICT'):
            profile.apply(self.db,self.payload,self.root/'backups',self.frontend)
        self.assertFalse((self.root/'backups').exists())

    def test_template_change_and_unknown_fields_block(self):
        changed = dict(self.payload,replacement={'name':'New','retired-phone':'123'})
        with self.assertRaisesRegex(ValueError,'CONFLICT'):
            profile.apply(self.db,changed,self.root/'backups',self.frontend)
        (self.frontend/'bio.html').write_text('<span data-page-text="new">Changed</span>')
        with self.assertRaisesRegex(ValueError,'CONFLICT'):
            profile.apply(self.db,self.payload,self.root/'backups',self.frontend)

    def test_insert_failure_rolls_back(self):
        with closing(sqlite3.connect(self.db)) as db:
            db.execute("CREATE TRIGGER reject_profile BEFORE INSERT ON profile_page_revisions BEGIN SELECT RAISE(ABORT,'test'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            profile.apply(self.db,self.payload,self.root/'backups',self.frontend)
        self.assertEqual(profile.page_state(self.db,'bio')['version'],1)

    def test_first_saved_resume(self):
        payload=dict(self.payload,page='resume',expected={'version':0,'fields':{}},
                     template_sha256=profile.template_info(self.frontend,'resume')[0])
        self.assertEqual(profile.apply(self.db,payload,self.root/'backups',self.frontend)['revision'],1)
        self.assertEqual(profile.page_state(self.db,'bio')['version'],1)
