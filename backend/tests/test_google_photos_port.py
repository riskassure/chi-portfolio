import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs,urlparse

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from flask import Flask
from routes.google_photos import google_photos_bp
from services.photography.google_photos_auth import GooglePhotosAuth,redirect_uri


class GooglePortTests(unittest.TestCase):
    def test_manage_assets_load_without_flask_static_route(self):
        app=Flask(__name__,static_folder=None,template_folder=str(Path(__file__).resolve().parents[1]/'src'/'templates'))
        app.secret_key='test';app.register_blueprint(google_photos_bp)
        with patch.dict(os.environ,{'PORTFOLIO_LOCAL_PORT':'5001','FLASK_ENV':'development'}):
            client=app.test_client()
            with client.session_transaction(base_url='http://127.0.0.1:5001') as session:
                session['is_admin']=True
            page=client.get('/api/photography/google/manage',base_url='http://127.0.0.1:5001')
            self.assertEqual(page.status_code,200)
            for filename,mime in [('google_photos.js','javascript'),('google_photos.css','text/css')]:
                url='/api/photography/google/assets/'+filename
                self.assertIn(url.encode(),page.data)
                asset=client.get(url,base_url='http://127.0.0.1:5001')
                self.assertEqual(asset.status_code,200)
                self.assertIn(mime,asset.content_type)
                self.assertTrue(asset.data)
                asset.close()
            self.assertEqual(client.get('/api/photography/google/assets/google-oauth.json',base_url='http://127.0.0.1:5001').status_code,404)

    def test_selected_port_used_and_wrong_host_rejected(self):
        app=Flask(__name__);app.secret_key='test';app.register_blueprint(google_photos_bp)
        with patch.dict(os.environ,{'PORTFOLIO_LOCAL_PORT':'5001','FLASK_ENV':'development'}):
            self.assertEqual(redirect_uri(),'http://127.0.0.1:5001/auth/google/callback')
            query=parse_qs(urlparse(GooglePhotosAuth().begin('test-client','browser')).query)
            self.assertEqual(query['redirect_uri'],[redirect_uri()])
            client=app.test_client()
            self.assertEqual(client.get('/api/photography/google/login',base_url='http://127.0.0.1:5001').status_code,200)
            self.assertEqual(client.get('/api/photography/google/login',base_url='http://127.0.0.1:5000').status_code,403)
            with patch.dict(os.environ,{'FLASK_ENV':'production'}):
                self.assertEqual(client.get('/api/photography/google/login',base_url='http://127.0.0.1:5001').status_code,403)
