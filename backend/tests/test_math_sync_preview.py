import sys
from pathlib import Path
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from preview_math_sync import compare

class SyncPreviewTests(unittest.TestCase):
    def test_three_way_decisions(self):
        base={k:{'title':'original'} for k in ('local','live','both','equal','delete')}
        local={k:dict(v) for k,v in base.items()}
        live={k:dict(v) for k,v in base.items()}
        local['local']['title']='new'
        live['live']['title']='Chi'
        local['both']['title']='local'; live['both']['title']='live'
        local['equal']['title']=live['equal']['title']='same'
        del local['delete']
        local['new']={'title':'new entry'}
        rows={r['canonical_name']:r for r in compare(base,local,live)['changes']}
        self.assertEqual(rows['live']['status'],'live_only_preserve')
        self.assertEqual(rows['local']['status'],'local_only_review')
        self.assertEqual(rows['both']['status'],'conflict')
        self.assertEqual(rows['equal']['status'],'already_equal')
        self.assertTrue(rows['delete']['requires_manual_deletion_review'])
        self.assertEqual(rows['new']['status'],'local_only_review')

    def test_deliberate_reversal_and_delete_edit_conflict(self):
        base={'entry':{'title':'Chi'}}
        local={'entry':{'title':'Chi-Chih'}}
        self.assertEqual(compare(base,local,base)['changes'][0]['status'],'local_only_review')
        self.assertEqual(compare(base,{},local)['changes'][0]['status'],'conflict')
        self.assertEqual(compare(base,base,base)['changes'],[])
