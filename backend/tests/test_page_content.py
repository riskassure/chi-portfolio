import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import re
import sqlite3
from contextlib import closing

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from app import app
from routes import page_content

class PageContentTests(unittest.TestCase):
    def test_permissions_persistence_conflicts_and_validation(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(page_content, 'DB_PATH', Path(temp)/'site.db'):
            client = app.test_client()
            self.assertEqual(client.get('/api/pages/bio').json, {'version':0,'fields':{}})
            self.assertEqual(client.put('/api/pages/bio',json={}).status_code,403)
            self.assertEqual(client.get('/api/pages/unknown').status_code,404)
            with client.session_transaction() as session: session['is_admin']=True
            fields = {key:'New text <script>literal</script>' for key in re.findall(r'data-page-text="([^"]+)"', (page_content.FRONTEND/'bio.html').read_text(encoding='utf-8'))}
            payload = {'version':0,'fields':fields}
            self.assertEqual(client.put('/api/pages/bio',json=payload).status_code,200)
            self.assertEqual(client.get('/api/pages/bio').json['fields'],fields)
            self.assertEqual(client.put('/api/pages/bio',json=payload).status_code,409)
            self.assertEqual(client.put('/api/pages/bio',json={'version':1,'fields':{'bad':'x'}}).status_code,400)
            payload['version']=1
            self.assertEqual(client.put('/api/pages/bio',json=payload,headers={'Origin':'https://attacker.example'}).status_code,403)
            self.assertEqual(client.put('/api/pages/bio',json=payload).status_code,200)
            with closing(sqlite3.connect(page_content.DB_PATH)) as db:
                self.assertEqual(db.execute('SELECT COUNT(*) FROM profile_page_revisions').fetchone()[0],2)

if __name__ == '__main__': unittest.main()
