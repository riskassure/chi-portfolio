"""Local Google Photos OAuth connection; credentials stay outside the served repository."""
import base64
import hashlib
import json
import os
from pathlib import Path
import secrets
import tempfile
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from config import PROJECT_ROOT

REDIRECT_URI = "http://127.0.0.1:5000/auth/google/callback"
SCOPES = "https://www.googleapis.com/auth/photospicker.mediaitems.readonly"


class GooglePhotosError(Exception):
    """A safe error message suitable for the local setup page."""


def credentials():
    path = Path(os.environ.get("GOOGLE_PHOTOS_CREDENTIALS", str(Path.home() / ".config/chi-portfolio/google-oauth.json"))).resolve()
    repository = PROJECT_ROOT
    if path.is_relative_to(repository):
        raise GooglePhotosError("Keep Google credentials outside the website repository.")
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))["web"]
        if not data.get("client_id") or not data.get("client_secret") or REDIRECT_URI not in data.get("redirect_uris", []):
            raise ValueError()
        return data
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        raise GooglePhotosError("Check the private google-oauth.json file and its authorized callback address.") from None


def token_path():
    base = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / ".local/share")))
    path = (base / "chi-portfolio" / "google-photos-tokens.json").resolve()
    if path.is_relative_to(PROJECT_ROOT):
        raise GooglePhotosError("Google tokens must stay outside the website repository.")
    return path


class GooglePhotosAuth:
    def __init__(self, path_factory=token_path):
        self.path_factory = path_factory
        self.pending = {}
        self.lock = threading.RLock()

    def begin(self, client_id, browser_id):
        with self.lock:
            now = time.time()
            self.pending = {k: v for k, v in self.pending.items() if v[0] > now}
            state = secrets.token_urlsafe(32)
            verifier = secrets.token_urlsafe(64)
            self.pending[state] = (now + 600, browser_id, client_id, verifier)
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
        return "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode({
            "client_id": client_id, "response_type": "code", "redirect_uri": REDIRECT_URI,
            "scope": SCOPES, "state": state, "access_type": "offline", "prompt": "consent", "code_challenge_method": "S256",
            "code_challenge": challenge,
        })

    def complete(self, state, browser_id, code, denied=False):
        with self.lock:
            pending = self.pending.pop(state, None)
            if not pending or pending[0] < time.time() or not secrets.compare_digest(pending[1].encode(), browser_id.encode()):
                raise GooglePhotosError("Authorization expired or did not match this browser. Please connect again.")
            if denied or not code:
                raise GooglePhotosError("Google Photos authorization was not completed. Please connect again.")
            _, _, client_id, verifier = pending
            data = self._request({"grant_type": "authorization_code", "code": code,
                                  "redirect_uri": REDIRECT_URI, "client_id": client_id,
                                  "code_verifier": verifier})
            self._save(data, client_id)

    def _request(self, payload):
        payload = {**payload, "client_secret": credentials()["client_secret"]}
        req = Request("https://oauth2.googleapis.com/token", data=urlencode(payload).encode(),
                      headers={"Content-Type": "application/x-www-form-urlencoded"})
        try:
            with urlopen(req, timeout=20) as response:
                return json.load(response)
        except HTTPError as exc:
            if exc.code == 400:
                raise GooglePhotosError("Google Photos rejected the authorization. Please connect again.") from None
            raise GooglePhotosError("Google Photos could not complete the request. Please try again later.") from None
        except (URLError, TimeoutError, ValueError):
            raise GooglePhotosError("Could not reach Google Photos or read its response. Please try again later.") from None

    def _read(self):
        try:
            data = json.loads(self.path_factory().read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError()
            return data
        except FileNotFoundError:
            return {}
        except (OSError, ValueError):
            raise GooglePhotosError("Could not read the local Google Photos connection file.") from None

    def _save(self, data, client_id, old=None):
        old = old or {}
        try:
            refresh = data.get("refresh_token") or old.get("refresh_token")
            access = data["access_token"]
            lifetime = int(data["expires_in"])
            scope = data.get("scope", old.get("scope", ""))
            if not access or not refresh or lifetime <= 0:
                raise ValueError()
            if not set(SCOPES.split()).issubset(scope.split()):
                raise GooglePhotosError("Required Google Photos permissions were not granted. Please connect again.")
        except (KeyError, TypeError, ValueError, AttributeError):
            raise GooglePhotosError("Google Photos returned an incomplete token response. Please connect again.") from None
        record = {"client_id": client_id, "access_token": access, "refresh_token": refresh,
                  "expires_at": time.time() + lifetime, "scope": scope}
        path = self.path_factory()
        temporary = None
        try:
            path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                             delete=False) as output:
                temporary = Path(output.name)
                json.dump(record, output)
            temporary.replace(path)
        except OSError:
            raise GooglePhotosError("Could not save the local Google Photos connection file.") from None
        finally:
            if temporary and temporary.exists():
                temporary.unlink()
        return access

    def access_token(self):
        """Refresh on demand; a rejected refresh requires browser authorization again."""
        with self.lock:
            old = self._read()
            if not old.get("refresh_token"):
                raise GooglePhotosError("Connect Google Photos first.")
            if old.get("client_id") != credentials()["client_id"]:
                raise GooglePhotosError("Google credentials changed. Please connect again.")
            if old.get("expires_at", 0) > time.time() + 60:
                return old["access_token"]
            data = self._request({"grant_type": "refresh_token", "refresh_token": old["refresh_token"],
                                  "client_id": old["client_id"]})
            return self._save(data, old["client_id"], old)

    def connected(self):
        data = self._read()
        return bool(data.get("refresh_token")) and data.get("client_id") == credentials()["client_id"]
