"""Occasional local-editor searches; no autocomplete or background geocoding."""
import json
import math
import os
from pathlib import Path
import sqlite3
from contextlib import closing
import threading
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen

LOCK = threading.Lock()
NEXT_REQUEST = 0.0


def cache_path():
    return Path(__file__).resolve().parents[3] / 'dist/place-search-cache.db'


def search(query):
    global NEXT_REQUEST
    if not isinstance(query, str) or not 2 <= len(query.strip()) <= 200:
        raise ValueError('Enter a place name between 2 and 200 characters.')
    query = ' '.join(query.split())
    endpoint = os.environ.get('PORTFOLIO_PLACE_SEARCH_URL', 'https://nominatim.openstreetmap.org/search')
    if not endpoint.startswith('https://'):
        raise RuntimeError('Place lookup is not configured. You can still choose a point on the map.')
    path = cache_path(); path.parent.mkdir(parents=True, exist_ok=True)
    with LOCK, closing(sqlite3.connect(path)) as conn:
        conn.execute('CREATE TABLE IF NOT EXISTS searches (provider TEXT, query TEXT, results TEXT, PRIMARY KEY(provider,query))')
        cached = conn.execute('SELECT results FROM searches WHERE provider=? AND query=?', (endpoint, query.casefold())).fetchone()
        if cached:
            return json.loads(cached[0])
        if time.monotonic() < NEXT_REQUEST:
            raise RuntimeError('Please wait a moment before searching again.')
        NEXT_REQUEST = time.monotonic() + 1.1
        request = Request(endpoint + '?' + urlencode({'q': query, 'format': 'jsonv2', 'limit': 5, 'accept-language': 'en'}),
                          headers={'User-Agent': 'ChiPortfolioTravelEditor/1.0 (+https://www.cwoo.me)', 'Accept': 'application/json'})
        try:
            with urlopen(request, timeout=15) as response:
                raw = response.read(131073)
            if len(raw) > 131072:
                raise ValueError()
            rows = json.loads(raw)
            if not isinstance(rows, list):
                raise ValueError()
            results = []
            for row in rows[:5]:
                name = row.get('display_name')
                lat, lon = float(row['lat']), float(row['lon'])
                if (isinstance(name, str) and name and math.isfinite(lat) and math.isfinite(lon)
                        and -90 <= lat <= 90 and -180 <= lon <= 180 and (lat, lon) != (0, 0)):
                    results.append({'name': name[:500], 'latitude': lat, 'longitude': lon})
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            raise RuntimeError('Place search is unavailable. Try again later or choose a point on the map.') from None
        finally:
            NEXT_REQUEST = time.monotonic() + 1.1
        conn.execute('INSERT OR REPLACE INTO searches VALUES (?,?,?)', (endpoint, query.casefold(), json.dumps(results)))
        conn.commit()
        return results
