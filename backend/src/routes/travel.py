"""Public map reads and local administrator edits; no database/schema changes."""
import math
from contextlib import closing
import os
from pathlib import Path
import re
import sqlite3
from flask import Blueprint, jsonify, request, session
from config import DB_PATH
from services import travel_store
import uuid

travel_bp = Blueprint('travel', __name__)


def key_path():
    return Path.home() / '.config' / 'chi-portfolio' / 'esri-api-key.txt'


@travel_bp.get('/api/travel/config')
def map_config():
    # This is a PUBLIC, referrer-restricted basemap credential, intentionally
    # supplied to the browser. Never put privileged ArcGIS credentials here.
    key = os.environ.get('ESRI_BASEMAP_API_KEY', '').strip()
    if not key:
        try:
            key = key_path().read_text(encoding='utf-8-sig').strip()
        except (OSError, UnicodeError):
            key = ''
    if not key or len(key) > 8192 or any(c.isspace() for c in key):
        response = jsonify(error='Map basemap access is not configured.')
        response.status_code = 503
    else:
        response = jsonify(apiKey=key)
    response.headers['Cache-Control'] = 'no-store'
    return response


def located(latitude, longitude):
    return (type(latitude) in (int, float) and type(longitude) in (int, float)
            and math.isfinite(latitude) and math.isfinite(longitude)
            and -90 <= latitude <= 90 and -180 <= longitude <= 180
            and (latitude, longitude) != (0, 0))


@travel_bp.get('/api/travel/photos')
def map_photos():
    try:
        # Read-only URI also prevents accidentally creating a missing database.
        with closing(sqlite3.connect(Path(DB_PATH).resolve().as_uri() + '?mode=ro', uri=True)) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute('SELECT image_id,file_path,title,location_name,latitude,longitude FROM photography_catalog ORDER BY image_id').fetchall()
        data, _ = travel_store.read()
        references = {name.casefold().strip(): point for point in data['locationReferences'] for name in point['names']}
        photos = []
        for row in rows:
            photo = dict(row)
            if not re.fullmatch(r'images/photography/[A-Za-z0-9_-]+\.(?:webp|jpg|jpeg|png)', photo['file_path'] or '', re.I):
                continue
            photo['located'] = located(photo['latitude'], photo['longitude'])
            photo['catalog_latitude'] = photo['latitude']
            photo['catalog_longitude'] = photo['longitude']
            photo['coordinate_source'] = 'Photo coordinates'
            point = data['photoLocations'].get(photo['file_path'])
            if point and (point['location_name'] != (photo['location_name'] or '')
                          or point.get('catalog_latitude') != photo['latitude']
                          or point.get('catalog_longitude') != photo['longitude']):
                point = None
            if not point and not photo['located']:
                point = references.get((photo['location_name'] or '').casefold().strip())
            if point:
                photo.update(latitude=point['latitude'], longitude=point['longitude'], located=True,
                             coordinate_source=point.get('description', 'Editor-selected map location'))
                photo['map_location_name'] = point.get('name') or photo['location_name']
            elif not photo['located']:
                photo['latitude'] = photo['longitude'] = None
            photos.append(photo)
        return jsonify(photos=photos)
    except (sqlite3.Error, OSError, ValueError):
        return jsonify(error='Photo locations are temporarily unavailable.'), 503


def editable():
    port = os.environ.get('PORTFOLIO_LOCAL_PORT', '5001')
    return (os.environ.get('FLASK_ENV') != 'production' and session.get('is_admin') is True
            and request.remote_addr in {'127.0.0.1', '::1'}
            and request.host in {f'127.0.0.1:{port}', f'localhost:{port}'})


@travel_bp.get('/api/travel/places')
def get_places():
    try:
        data, revision = travel_store.read()
        return jsonify(data=data, revision=revision, editable=editable(), cities=travel_store.cities(),
                       regions=travel_store.selected_regions(data), regionOptions=travel_store.region_options())
    except (OSError, ValueError):
        return jsonify(error='Could not read map places.'), 503


@travel_bp.post('/api/travel/places')
def save_place():
    if not editable() or request.headers.get('Origin') != request.host_url.rstrip('/'):
        return jsonify(error='Sign in on the local website to edit map places.'), 403
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify(error='Expected a map edit.'), 400
    try:
        with travel_store.edit(body.get('revision')) as data:
            action = body.get('action')
            if action == 'regions':
                regions = body.get('regions')
                options = travel_store.region_options()
                if not isinstance(regions, dict) or set(regions) != set(options):
                    raise ValueError('Invalid regions.')
                for group, values in regions.items():
                    known = {r['code'] for r in options[group]}
                    if (not isinstance(values, list) or any(not isinstance(v, str) or v not in known for v in values)
                            or len(values) != len(set(values))):
                        raise ValueError('Invalid regions.')
                data['regions'] = regions
            elif action == 'cities':
                visits = body.get('visits')
                known = {c['id'] for c in travel_store.cities()}
                if not isinstance(visits, dict) or any(k not in known or v not in ('visited', 'not-visited', 'unsure') for k, v in visits.items()):
                    raise ValueError('Invalid city review.')
                data['cityVisits'] = visits
            elif action == 'delete':
                place_id = body.get('id')
                if not any(p['id'] == place_id for p in data['places']):
                    raise ValueError('Place no longer exists.')
                data['places'] = [p for p in data['places'] if p['id'] != place_id]
            elif action in ('place', 'photo'):
                lat, lon = body.get('latitude'), body.get('longitude')
                if not located(lat, lon):
                    raise ValueError('Choose a valid point on the map or enter latitude and longitude.')
                if action == 'photo':
                    path = body.get('file_path')
                    with closing(sqlite3.connect(Path(DB_PATH).resolve().as_uri() + '?mode=ro', uri=True)) as conn:
                        row = conn.execute('SELECT location_name,latitude,longitude FROM photography_catalog WHERE file_path=?', (path,)).fetchone()
                    if not row or (row[0] or '') != body.get('location_name'):
                        raise ValueError('The photo location text changed. Reload before placing it.')
                    if row[1:] != (body.get('catalog_latitude'), body.get('catalog_longitude')):
                        raise ValueError('Photo coordinates changed. Reload before placing it.')
                    name = body.get('name', row[0] or 'Photo location')
                    if not isinstance(name, str) or not 1 <= len(name.strip()) <= 200:
                        raise ValueError('Enter a place name (up to 200 characters).')
                    data['photoLocations'][path] = {'latitude': lat, 'longitude': lon, 'location_name': row[0] or '',
                                                   'catalog_latitude': row[1], 'catalog_longitude': row[2], 'name': name.strip()}
                else:
                    name = body.get('name')
                    if not isinstance(name, str) or not 1 <= len(name.strip()) <= 200:
                        raise ValueError('Enter a place name (up to 200 characters).')
                    place_id = body.get('id')
                    if place_id and not any(p['id'] == place_id for p in data['places']):
                        raise ValueError('Place no longer exists.')
                    place_id = place_id or 'place-' + uuid.uuid4().hex
                    data['places'] = [p for p in data['places'] if p['id'] != place_id]
                    data['places'].append({'id': place_id, 'name': name.strip(), 'latitude': lat, 'longitude': lon, 'kind': 'place'})
            else:
                raise ValueError('Unknown map edit.')
        return get_places()
    except travel_store.Conflict as error:
        return jsonify(error=str(error)), 409
    except (ValueError, TypeError):
        return jsonify(error='Invalid or outdated map edit. Check the name and coordinates, or reload the page.'), 400
    except (OSError, sqlite3.Error):
        return jsonify(error='Could not save map places. Your previous file has been kept.'), 503
