"""Local map editing stored in a reviewable, publishable JavaScript data file."""
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
from services.file_persistence import exclusive_edit, replace_text

ROOT = Path(__file__).resolve().parents[3]
PREFIX = 'window.TRAVEL_PLACES = '


def data_path():
    return ROOT / 'frontend/geography/places-data.js'


def read_assignment(path, prefix):
    raw = path.read_bytes()
    text = raw.decode('utf-8').strip()
    if not text.startswith(prefix) or not text.endswith(';'):
        raise ValueError('Invalid map data file.')
    return json.loads(text[len(prefix):-1]), hashlib.sha256(raw).hexdigest()


def read():
    return read_assignment(data_path(), PREFIX)


def cities():
    return read_assignment(ROOT / 'frontend/geography/city-reference.js', 'window.TRAVEL_CITIES = ')[0]


def region_options():
    return read_assignment(ROOT / 'frontend/geography/region-reference.js', 'window.TRAVEL_REGIONS = ')[0]


def selected_regions(data):
    return data.get('regions', {
        'US': [r['code'] for r in region_options()['US'] if r['code'] not in ('AK', 'ID')],
        'CA': [],
        'countries': ['USA', 'TWN', 'CHN', 'VNM', 'FRA', 'CHE', 'DEU', 'GBR', 'ITA', 'CAN'],
    })


class Conflict(Exception):
    pass


@contextmanager
def edit(revision):
    target = data_path()
    with exclusive_edit(target, Conflict, 'Another map edit is in progress. Reload and try again.'):
        data, current = read()
        if revision != current:
            raise Conflict('The map data changed. Reload before saving your edit.')
        yield data
        content = PREFIX + json.dumps(data, ensure_ascii=True, indent=2, allow_nan=False) + ';\n'
        # Preserve the map's revision check after editor validation/serialization.
        if read()[1] != current:
            raise Conflict('The map data changed. Reload before saving your edit.')
        replace_text(target, content, prefix='.travel-')
