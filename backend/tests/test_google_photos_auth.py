import base64
import hashlib
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from flask import Flask
from routes.google_photos import google_photos_bp
from services.photography.google_photos_auth import REDIRECT_URI, SCOPES, GooglePhotosAuth, GooglePhotosError


class GooglePhotosTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "tokens.json"
        self.auth = GooglePhotosAuth(lambda: self.path)
        app = Flask(__name__)
        app.secret_key = "test-only"
        app.config["ADMIN_PASSWORD"] = "test-admin-password"
        app.register_blueprint(google_photos_bp)
        self.client = app.test_client()
        self.base = "http://127.0.0.1:5000"
        self.patcher = patch("routes.google_photos.auth", self.auth)
        self.patcher.start()
        for target in ('services.photography.google_photos_auth.credentials', 'routes.google_photos.credentials'):
            mock = patch(target, return_value={'client_id': 'a' * 32, 'client_secret': 'test-secret'})
            mock.start()
            self.addCleanup(mock.stop)
        self.addCleanup(self.patcher.stop)
        with self.client.session_transaction(base_url=self.base) as session:
            session["is_admin"] = True

    def response(self, **changes):
        return dict(access_token="access", refresh_token="refresh", expires_in=3600,
                    scope=SCOPES, **changes)

    def begin(self):
        url = self.auth.begin("a" * 32, "browser")
        return parse_qs(urlparse(url).query)

    def test_pkce_and_callback_single_use(self):
        query = self.begin()
        state = query["state"][0]
        verifier = self.auth.pending[state][3]
        expected = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
        self.assertEqual(query["code_challenge"], [expected])
        self.assertEqual(query["redirect_uri"], [REDIRECT_URI])
        with patch.object(self.auth, "_request", return_value=self.response()) as exchange:
            self.auth.complete(state, "browser", "code")
            self.assertEqual(exchange.call_args.args[0]["code_verifier"], verifier)
            with self.assertRaises(GooglePhotosError):
                self.auth.complete(state, "browser", "code")
            self.assertEqual(exchange.call_count, 1)
        self.assertEqual(self.auth.access_token(), "access")

    def test_invalid_expired_wrong_browser_and_denied_do_not_exchange(self):
        with patch.object(self.auth, "_request") as exchange:
            for kind in ("unknown", "expired", "wrong_browser", "denied"):
                state = self.begin()["state"][0]
                if kind == "expired":
                    self.auth.pending[state] = (0, *self.auth.pending[state][1:])
                with self.assertRaises(GooglePhotosError):
                    self.auth.complete("unknown" if kind == "unknown" else state,
                                       "other" if kind == "wrong_browser" else "browser",
                                       "code", denied=kind == "denied")
            exchange.assert_not_called()
        self.assertFalse(self.path.exists())

    def test_refresh_preserves_or_rotates_refresh_token(self):
        self.auth._save(self.response(), "a" * 32)
        for replacement in (None, "rotated"):
            old = self.auth._read()
            old["expires_at"] = 0
            import json
            self.path.write_text(json.dumps(old))
            data = {"access_token": "new", "expires_in": 3600}
            if replacement:
                data["refresh_token"] = replacement
            with patch.object(self.auth, "_request", return_value=data) as exchange:
                self.assertEqual(self.auth.access_token(), "new")
                self.assertEqual(exchange.call_args.args[0]["grant_type"], "refresh_token")
            self.assertEqual(self.auth._read()["refresh_token"], replacement or "refresh")

    def test_bad_token_response_preserves_previous_connection(self):
        self.auth._save(self.response(), "a" * 32)
        before = self.path.read_bytes()
        for data in ({}, {"access_token": "x", "expires_in": 3600, "refresh_token": "r", "scope": ""}):
            with self.assertRaises(GooglePhotosError):
                self.auth._save(data, "a" * 32)
        self.assertEqual(self.path.read_bytes(), before)

    def test_browser_roundtrip_and_access_controls(self):
        path = '/api/photography/google/connect'
        self.assertEqual(self.client.get(path, base_url='http://evil.example:5000').status_code, 403)
        self.assertEqual(self.client.post(path, base_url=self.base).status_code, 400)
        page = self.client.get(path, base_url=self.base)
        self.assertEqual(page.status_code, 200)
        self.assertNotIn('test-secret', page.text)
        with self.client.session_transaction(base_url=self.base) as session:
            csrf = session['google_photos_csrf']
        response = self.client.post(path, base_url=self.base, data={'csrf': csrf})
        self.assertEqual(response.status_code, 303)
        query = parse_qs(urlparse(response.location).query)
        self.assertEqual(query['scope'], [SCOPES])
        with patch.object(self.auth, '_request', return_value=self.response()):
            response = self.client.get('/auth/google/callback', base_url=self.base,
                query_string={'state': query['state'][0], 'code': 'code'})
        self.assertEqual(response.status_code, 302)
        status = self.client.get('/api/photography/google/status', base_url=self.base)
        self.assertEqual(status.json, {'connected': True})
        self.assertEqual(status.headers['Cache-Control'], 'no-store')
        with self.client.session_transaction(base_url=self.base) as session:
            session.clear()
        self.assertEqual(self.client.get('/api/photography/google/status', base_url=self.base).status_code, 403)

    def test_login_requires_csrf_and_password(self):
        with self.client.session_transaction(base_url=self.base) as session:
            session.clear()
        path = '/api/photography/google/login'
        self.assertEqual(self.client.post(path, base_url=self.base, data={'password': 'test-admin-password'}).status_code, 400)
        with self.client.session_transaction(base_url=self.base) as session:
            csrf = session['google_photos_csrf']
        self.assertEqual(self.client.post(path, base_url=self.base, data={'csrf': csrf, 'password': 'wrong'}).status_code, 400)
        self.assertEqual(self.client.post(path, base_url=self.base, data={'csrf': csrf, 'password': 'test-admin-password'}).status_code, 303)

if __name__ == '__main__':
    unittest.main()
