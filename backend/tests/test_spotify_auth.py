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
from routes.music_spotify import spotify_bp
from services.music.spotify_auth import REDIRECT_URI, SCOPES, SpotifyAuth, SpotifyError


class SpotifyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "tokens.json"
        self.auth = SpotifyAuth(lambda: self.path)
        app = Flask(__name__)
        app.secret_key = "test-only"
        app.config["ADMIN_PASSWORD"] = "test-admin-password"
        app.register_blueprint(spotify_bp)
        self.client = app.test_client()
        self.base = "http://127.0.0.1:5000"
        self.patcher = patch("routes.music_spotify.auth", self.auth)
        self.patcher.start()
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
            with self.assertRaises(SpotifyError):
                self.auth.complete(state, "browser", "code")
            self.assertEqual(exchange.call_count, 1)
        self.assertEqual(self.auth.access_token(), "access")

    def test_invalid_expired_wrong_browser_and_denied_do_not_exchange(self):
        with patch.object(self.auth, "_request") as exchange:
            for kind in ("unknown", "expired", "wrong_browser", "denied"):
                state = self.begin()["state"][0]
                if kind == "expired":
                    self.auth.pending[state] = (0, *self.auth.pending[state][1:])
                with self.assertRaises(SpotifyError):
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
            with self.assertRaises(SpotifyError):
                self.auth._save(data, "a" * 32)
        self.assertEqual(self.path.read_bytes(), before)

    def test_routes_require_local_admin_and_csrf(self):
        path = "/api/music/spotify/connect"
        self.assertEqual(self.client.get(path, base_url="http://evil.example:5000").status_code, 403)
        self.assertEqual(self.client.get(path, base_url=self.base,
                                        environ_overrides={"REMOTE_ADDR": "192.0.2.1"}).status_code, 403)
        self.assertEqual(self.client.post(path, base_url=self.base, data={"client_id": "a" * 32}).status_code, 400)
        with self.client.session_transaction(base_url=self.base) as session:
            session.clear()
        self.assertEqual(self.client.get(path, base_url=self.base).status_code, 302)

    def test_local_login_requires_password_and_csrf_then_connects(self):
        with self.client.session_transaction(base_url=self.base) as session:
            session.clear()
        path = "/api/music/spotify/login"
        self.assertEqual(self.client.get(path, base_url="http://evil.example:5000").status_code, 403)
        response = self.client.post(path, base_url=self.base, data={"password": "test-admin-password"})
        self.assertEqual(response.status_code, 400)
        for password, expected in (("wrong", 401), ("test-admin-password", 303)):
            self.client.get(path, base_url=self.base)
            with self.client.session_transaction(base_url=self.base) as session:
                csrf = session["spotify_login_csrf"]
            response = self.client.post(path, base_url=self.base,
                                        data={"csrf": csrf, "password": password})
            self.assertEqual(response.status_code, expected)
        response = self.client.get(response.location, base_url=self.base)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Client ID", response.text)

    def test_existing_admin_session_skips_login(self):
        response = self.client.get("/api/music/spotify/login", base_url=self.base)
        self.assertEqual(response.location, "/api/music/spotify/connect")

    def test_connection_form_survives_another_tab_and_invalid_submission(self):
        path = "/api/music/spotify/connect"
        self.client.get(path, base_url=self.base)
        with self.client.session_transaction(base_url=self.base) as session:
            csrf = session["spotify_form_token"]
        self.client.get(path, base_url=self.base)
        bad = self.client.post(path, base_url=self.base, data={"csrf": csrf, "client_id": "invalid"})
        self.assertEqual(bad.status_code, 400)
        response = self.client.post(path, base_url=self.base, data={"csrf": csrf, "client_id": "a" * 32})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.startswith("https://accounts.spotify.com/authorize?"))
        self.assertIn("form-action 'self' https://accounts.spotify.com;", response.headers["Content-Security-Policy"])

    def test_stale_form_renders_retry_without_starting_authorization(self):
        path = "/api/music/spotify/connect"
        response = self.client.post(path, base_url=self.base,
                                    data={"csrf": "stale", "client_id": "a" * 32})
        self.assertEqual(response.status_code, 400)
        self.assertIn('value="' + "a" * 32 + '"', response.text)
        self.assertIn('name="csrf"', response.text)
        self.assertEqual(self.auth.pending, {})
        with self.client.session_transaction(base_url=self.base) as session:
            csrf = session["spotify_form_token"]
        response = self.client.post(path, base_url=self.base, data={"csrf": csrf, "client_id": "a" * 32})
        self.assertEqual(response.status_code, 302)

    def test_browser_connection_and_private_status(self):
        page = self.client.get("/api/music/spotify/connect", base_url=self.base)
        self.assertEqual(page.status_code, 200)
        self.assertEqual(page.headers["Cache-Control"], "no-store")
        with self.client.session_transaction(base_url=self.base) as session:
            csrf = session["spotify_form_token"]
        response = self.client.post("/api/music/spotify/connect", base_url=self.base,
                                    data={"csrf": csrf, "client_id": "a" * 32})
        query = parse_qs(urlparse(response.location).query)
        with patch.object(self.auth, "_request", return_value=self.response()):
            response = self.client.get("/api/music/spotify/callback", base_url=self.base,
                                       query_string={"state": query["state"][0], "code": "code"})
        self.assertEqual(response.status_code, 302)
        status = self.client.get(response.location, base_url=self.base)
        self.assertTrue(status.json["connected"])
        self.assertNotIn("access_token", status.text)
        self.assertNotIn("refresh_token", status.text)


if __name__ == "__main__":
    unittest.main()
