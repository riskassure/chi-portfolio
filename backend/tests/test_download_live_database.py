from contextlib import closing
import hashlib
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from download_live_database import download, verify


class DownloadTests(unittest.TestCase):
    def test_verified_download_and_unique_destination(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); source=root/'original.db'
            with closing(sqlite3.connect(source)) as db:
                db.execute('CREATE TABLE math_concepts(id INTEGER)'); db.commit()
            digest=hashlib.sha256(source.read_bytes()).hexdigest()
            def run(args,**kwargs):
                if args[0]=='ssh':
                    return subprocess.CompletedProcess(args,0,'SNAPSHOT_SHA256='+digest+'\n')
                shutil.copyfile(source,args[-1])
                return subprocess.CompletedProcess(args,0)
            with patch('download_live_database.subprocess.run',side_effect=run), patch('download_live_database.shutil.which',return_value='available'), patch('builtins.print'):
                first=download(root/'downloads')
                second=download(root/'downloads')
            self.assertNotEqual(first,second)
            self.assertEqual(first.read_bytes(),source.read_bytes())
            self.assertTrue((first.parent/'snapshot.json').exists())
            self.assertFalse((first.parent/'download.partial').exists())
            with self.assertRaises(ValueError): verify(first,'0'*64)

    def test_auth_failure_stops_before_download(self):
        with tempfile.TemporaryDirectory() as temp, patch('download_live_database.shutil.which',return_value='available'), patch('download_live_database.subprocess.run',side_effect=subprocess.CalledProcessError(255,'ssh')) as run, patch('builtins.print'):
            with self.assertRaises(subprocess.CalledProcessError): download(Path(temp))
            self.assertEqual(run.call_count,1)
            self.assertEqual(list(Path(temp).rglob('live-snapshot.db')),[])
