"""Read-only Spotify API client with bounded pagination and safe failures."""
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from services.music.spotify_auth import SpotifyAuth, SpotifyError


class SpotifyApiError(SpotifyError):
    def __init__(self, status, retry_after=0):
        self.status = status
        self.retry_after = retry_after
        super().__init__(f"Spotify API returned HTTP {status}. " +
                         ("Reconnect Spotify." if status == 401 else "The previous catalog is retained; try later."))


class SpotifyApi:
    def __init__(self, auth=None):
        self.auth = auth or SpotifyAuth()

    def get(self, url):
        if url.startswith("/"):
            url = "https://api.spotify.com/v1" + url
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.netloc != "api.spotify.com" or not parsed.path.startswith("/v1/"):
            raise SpotifyError("Unexpected Spotify pagination address.")
        req = Request(url, headers={"Authorization": "Bearer " + self.auth.access_token()})
        try:
            with urlopen(req, timeout=30) as response:
                result = json.load(response)
                if not isinstance(result, dict):
                    raise ValueError()
                return result
        except HTTPError as exc:
            retry = exc.headers.get("Retry-After", "0")
            raise SpotifyApiError(exc.code, int(retry) if retry.isdigit() else 3600) from None
        except (URLError, TimeoutError, ValueError):
            raise SpotifyError("Spotify network request failed. The previous catalog is retained.") from None

    def items(self, url):
        seen = set()
        while url:
            if url in seen or len(seen) >= 1000:
                raise SpotifyError("Spotify pagination did not complete.")
            seen.add(url)
            page = self.get(url)
            if not isinstance(page.get("items"), list):
                raise SpotifyError("Spotify returned an incomplete page.")
            yield from page["items"]
            url = page.get("next")
