from contextlib import closing
import hashlib
from io import BytesIO
import json
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PIL import Image
import photo_sync as photos
from inspect_staged_package import preview
from live_math_publication import publish


class PhotoSyncTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.db=self.root/'backend'/'portfolio.db';self.db.parent.mkdir()
        self.front=self.root/'frontend';self.front.mkdir()
        with closing(sqlite3.connect(self.db)) as db:
            db.execute('CREATE TABLE photography_catalog(image_id INTEGER PRIMARY KEY, file_path TEXT UNIQUE,title TEXT,location_name TEXT,latitude REAL,longitude REAL,is_currently_displayed INTEGER,display_count INTEGER)')
        buf=BytesIO();Image.new('RGB',(20,10),'green').save(buf,'WEBP');self.image=buf.getvalue()
        self.payload=dict(kind='photo-add',sha256=hashlib.sha256(self.image).hexdigest(),photo=dict(
            file_path='images/photography/test.webp',title='Test photo',location_name='Garden',latitude=0,longitude=0,is_currently_displayed=1))

    def test_publication_backup_and_idempotence(self):
        self.assertTrue(photos.status(self.db,self.payload,self.image,self.front).startswith('NO DUPLICATE'))
        result=photos.apply(self.db,self.payload,self.image,self.root/'backups',self.front)
        self.assertEqual(result['status'],'APPLIED')
        self.assertEqual(photos.catalog(Path(result['backup'])),{})
        self.assertEqual((self.front/self.payload['photo']['file_path']).read_bytes(),self.image)
        self.assertEqual(photos.catalog(self.db)[self.payload['photo']['file_path']],self.payload['photo'])
        self.assertEqual(photos.apply(self.db,self.payload,self.image,self.root/'backups',self.front)['status'],'ALREADY_PRESENT')
        self.assertEqual(len(list((self.root/'backups').iterdir())),1)

    def test_conflicting_file_is_never_overwritten(self):
        target=self.front/self.payload['photo']['file_path'];target.parent.mkdir(parents=True);target.write_bytes(b'existing')
        with self.assertRaisesRegex(ValueError,'CONFLICT'):
            photos.apply(self.db,self.payload,self.image,self.root/'backups',self.front)
        self.assertEqual(target.read_bytes(),b'existing');self.assertEqual(photos.catalog(self.db),{})

    def test_failed_insert_leaves_retryable_image_but_no_row(self):
        with closing(sqlite3.connect(self.db)) as db:
            db.execute("CREATE TRIGGER reject_photo BEFORE INSERT ON photography_catalog BEGIN SELECT RAISE(ABORT,'test'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            photos.apply(self.db,self.payload,self.image,self.root/'backups',self.front)
        self.assertEqual(photos.catalog(self.db),{})
        with closing(sqlite3.connect(self.db)) as db:db.execute('DROP TRIGGER reject_photo')
        self.assertEqual(photos.apply(self.db,self.payload,self.image,self.root/'backups',self.front)['status'],'APPLIED')

    def test_prepare_preview_and_dispatch(self):
        working=self.root/'working.db';shutil.copyfile(self.db,working)
        target=self.front/self.payload['photo']['file_path'];target.parent.mkdir(parents=True);target.write_bytes(self.image)
        with closing(sqlite3.connect(working)) as db:
            db.execute('INSERT INTO photography_catalog('+','.join(photos.FIELDS)+',display_count) VALUES(?,?,?,?,?,?,0)',tuple(self.payload['photo'][k] for k in photos.FIELDS));db.commit()
        package=self.root/'package.zip'
        photos.prepare(self.db,working,self.payload['photo']['file_path'],self.front,package)
        self.assertIn('Test photo',preview(package.read_bytes()))
        self.assertEqual(publish(package.read_bytes(),self.db,self.root/'backups',self.db.parent/'src')['status'],'APPLIED')

    def test_checksum_and_traversal_rejected(self):
        with self.assertRaises(ValueError):photos.validate(self.payload,b'not a webp')
        payload=dict(self.payload,photo=dict(self.payload['photo'],file_path='../escape.webp'))
        with self.assertRaises(ValueError):photos.validate(payload,self.image)
        with self.assertRaises(ValueError):photos.validate(dict(self.payload,sha256='0'*64),self.image)
