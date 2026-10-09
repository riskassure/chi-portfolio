import io
from pathlib import Path
import sys
import unittest
from unittest.mock import patch, MagicMock
from urllib.error import HTTPError

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pythonanywhere_api import get_account_info, NoRedirects


class ApiTests(unittest.TestCase):
    def test_get_only_and_fixed_host(self):
        opener=MagicMock()
        opener.open.return_value.__enter__.return_value=io.StringIO('{"daily_cpu_limit_seconds":5000}')
        with patch('pythonanywhere_api.build_opener',return_value=opener):
            result=get_account_info({'username':'cwoo','token':'test-token'},'cpu')
        req=opener.open.call_args.args[0]
        self.assertEqual(req.get_method(),'GET')
        self.assertEqual(req.full_url,'https://www.pythonanywhere.com/api/v0/user/cwoo/cpu/')
        self.assertEqual(result['daily_cpu_limit_seconds'],5000)
        with self.assertRaises(ValueError):get_account_info({'username':'cwoo','token':'test-token'},'reload')

    def test_error_redaction_and_redirect_block(self):
        opener=MagicMock()
        opener.open.side_effect=HTTPError('https://example',403,'private server detail',{},None)
        with patch('pythonanywhere_api.build_opener',return_value=opener):
            with self.assertRaises(RuntimeError) as caught:get_account_info({'username':'cwoo','token':'secret-value'},'cpu')
        self.assertNotIn('secret-value',str(caught.exception))
        self.assertNotIn('private server detail',str(caught.exception))
        self.assertIsNone(NoRedirects().redirect_request(None,None,302,'',{},'https://elsewhere'))
