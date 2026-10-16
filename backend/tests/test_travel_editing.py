from contextlib import closing
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch
from flask import Flask

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from routes import travel
from services import travel_store

ORIGIN = 'http://127.0.0.1:5001'


class TravelEditingTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.path = self.root / 'places.js'
        self.path.write_text(travel_store.PREFIX + json.dumps({'places': [], 'photoLocations': {}, 'cityVisits': {}, 'locationReferences': []}) + ';\n')
        self.db = self.root / 'photos.db'
        with closing(sqlite3.connect(self.db)) as conn:
            conn.execute('CREATE TABLE photography_catalog(image_id,file_path,title,location_name,latitude,longitude)')
            conn.execute("INSERT INTO photography_catalog VALUES(1,'images/photography/test.webp','My title','Unknown Location',0,0)")
            conn.commit()
        for patcher in [patch.object(travel_store, 'data_path', return_value=self.path), patch.object(travel, 'DB_PATH', self.db),
                        patch.dict(os.environ, {'FLASK_ENV': 'development', 'PORTFOLIO_LOCAL_PORT': '5001'})]:
            patcher.start(); self.addCleanup(patcher.stop)
        app = Flask(__name__); app.secret_key = 'dummy-test-session'; app.register_blueprint(travel.travel_bp)
        self.client = app.test_client()
        self.login()

    def login(self):
        with self.client.session_transaction(base_url=ORIGIN) as session:
            session['is_admin'] = True

    def post(self, body, **kwargs):
        body = {'revision': travel_store.read()[1], **body}
        return self.client.post('/api/travel/places', base_url=ORIGIN, headers={'Origin': ORIGIN}, json=body, **kwargs)

    def test_add_edit_delete_and_stale_revision(self):
        revision = travel_store.read()[1]
        result = self.post({'action': 'place', 'name': 'A place', 'latitude': 30, 'longitude': 40})
        self.assertEqual(result.status_code, 200)
        place = result.json['data']['places'][0]
        result = self.post({'action': 'place', 'revision': revision, 'name': 'Lost edit', 'latitude': 31, 'longitude': 41})
        self.assertEqual(result.status_code, 409)
        result = self.post({'action': 'place', 'id': place['id'], 'name': 'Renamed', 'latitude': 32, 'longitude': 42})
        self.assertEqual(result.json['data']['places'][0]['name'], 'Renamed')
        self.assertEqual(len(result.json['data']['places']), 1)
        result = self.post({'action': 'delete', 'id': place['id']})
        self.assertEqual(result.json['data']['places'], [])

    def test_photo_binding_preserves_database_and_tracks_current_metadata(self):
        before = self.db.read_bytes()
        body = {'action': 'photo', 'file_path': 'images/photography/test.webp', 'location_name': 'Unknown Location',
                'name': 'Glade Creek', 'catalog_latitude': 0, 'catalog_longitude': 0, 'latitude': 38.1, 'longitude': -81.1}
        self.assertEqual(self.post(body).status_code, 200)
        photo = self.client.get('/api/travel/photos').json['photos'][0]
        self.assertTrue(photo['located']); self.assertEqual(photo['latitude'], 38.1)
        self.assertEqual(photo['map_location_name'], 'Glade Creek')
        self.assertEqual(photo['location_name'], 'Unknown Location')
        self.assertEqual(self.post({**body, 'name': ' '}).status_code, 400)
        self.assertEqual(photo['title'], 'My title'); self.assertEqual(photo['catalog_latitude'], 0)
        self.assertEqual(self.db.read_bytes(), before)
        with closing(sqlite3.connect(self.db)) as conn:
            conn.execute("UPDATE photography_catalog SET location_name='New location'"); conn.commit()
        self.assertFalse(self.client.get('/api/travel/photos').json['photos'][0]['located'])
        self.assertEqual(self.post(body).status_code, 400)

    def test_override_valid_coordinates_then_catalog_edit_wins(self):
        with closing(sqlite3.connect(self.db)) as conn:
            conn.execute('UPDATE photography_catalog SET latitude=10,longitude=20'); conn.commit()
        body = {'action': 'photo', 'file_path': 'images/photography/test.webp', 'location_name': 'Unknown Location',
                'catalog_latitude': 10, 'catalog_longitude': 20, 'latitude': 30, 'longitude': 40}
        self.assertEqual(self.post(body).status_code, 200)
        self.assertEqual(self.client.get('/api/travel/photos').json['photos'][0]['latitude'], 30)
        with closing(sqlite3.connect(self.db)) as conn:
            conn.execute('UPDATE photography_catalog SET latitude=11'); conn.commit()
        self.assertEqual(self.client.get('/api/travel/photos').json['photos'][0]['latitude'], 11)
        self.assertEqual(self.post(body).status_code, 400)

    def test_general_location_reference_and_owner_pin_precedence(self):
        data, revision = travel_store.read()
        with travel_store.edit(revision) as data:
            data['locationReferences'].append({'names': ['Unknown Location'], 'latitude': 5, 'longitude': 6, 'description': 'General reference'})
        self.assertEqual(self.client.get('/api/travel/photos').json['photos'][0]['latitude'], 5)
        self.assertEqual(self.post({'action': 'photo', 'file_path': 'images/photography/test.webp', 'location_name': 'Unknown Location',
                                  'catalog_latitude': 0, 'catalog_longitude': 0, 'latitude': 7, 'longitude': 8}).status_code, 200)
        self.assertEqual(self.client.get('/api/travel/photos').json['photos'][0]['latitude'], 7)

    def test_security_requires_local_admin_and_same_origin(self):
        before = self.path.read_bytes()
        body = {'action': 'place', 'name': 'Blocked', 'latitude': 1, 'longitude': 2, 'revision': travel_store.read()[1]}
        with self.client.session_transaction(base_url=ORIGIN) as session: session.clear()
        self.assertEqual(self.post(body).status_code, 403)
        self.login()
        for headers in [{}, {'Origin': 'https://evil.example'}]:
            self.assertEqual(self.client.post('/api/travel/places', base_url=ORIGIN, headers=headers, json=body).status_code, 403)
        self.assertEqual(self.post(body, environ_overrides={'REMOTE_ADDR': '10.0.0.4'}).status_code, 403)
        with patch.dict(os.environ, {'FLASK_ENV': 'production'}):
            self.assertEqual(self.post(body).status_code, 403)
            self.assertFalse(self.client.get('/api/travel/places', base_url=ORIGIN).json['editable'])
        self.assertEqual(before, self.path.read_bytes())

    def test_invalid_input_and_write_failure_preserve_previous_file(self):
        before = self.path.read_bytes()
        for lat, lon in [(91, 0), (0, 181), (0, 0), (True, 2), ('1', 2), (None, 2)]:
            self.assertEqual(self.post({'action': 'place', 'name': 'Bad', 'latitude': lat, 'longitude': lon}).status_code, 400)
        self.assertEqual(self.post({'action': 'place', 'name': '', 'latitude': 1, 'longitude': 2}).status_code, 400)
        with patch.object(travel_store.os, 'replace', side_effect=OSError('test disk failure')):
            self.assertEqual(self.post({'action': 'place', 'name': 'Cannot save', 'latitude': 1, 'longitude': 2}).status_code, 503)
        self.assertEqual(before, self.path.read_bytes())
        self.assertFalse(self.path.with_suffix('.lock').exists())
        self.assertEqual(list(self.root.glob('.travel-*')), [])

    def test_regions_defaults_validation_and_preservation(self):
        state = self.client.get('/api/travel/places').json
        self.assertEqual(len(state['regions']['US']), 48)
        self.assertEqual(state['regions']['CA'], [])
        self.assertEqual(len(state['regions']['countries']), 10)
        self.assertEqual(len(state['regionOptions']['CA']), 13)
        self.post({'action': 'place', 'name': 'Keep me', 'latitude': 1, 'longitude': 2})
        before = travel_store.read()[0]
        revision = travel_store.read()[1]
        regions = {'US': ['ID'], 'CA': ['ON', 'BC'], 'countries': ['JPN', 'CAN']}
        result = self.post({'action': 'regions', 'regions': regions})
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json['regions'], regions)
        for key in before:
            self.assertEqual(result.json['data'][key], before[key])
        self.assertEqual(self.post({'action': 'regions', 'regions': regions, 'revision': revision}).status_code, 409)
        saved = self.path.read_bytes()
        for invalid in [{}, {**regions, 'CA': ['XX']}, {**regions, 'US': ['ID', 'ID']}, {**regions, 'CA': [False]}]:
            self.assertEqual(self.post({'action': 'regions', 'regions': invalid}).status_code, 400)
        self.assertEqual(saved, self.path.read_bytes())
        empty = {'US': [], 'CA': [], 'countries': []}
        self.assertEqual(self.post({'action': 'regions', 'regions': empty}).json['regions'], empty)


    def test_city_statuses_only_for_reviewed_known_cities(self):
        cities = travel_store.cities()
        self.assertEqual(len(cities), 159)
        self.assertEqual({c['name'] for c in cities if c['previouslyExcluded']}, {'Nashville', 'Boise', 'Anchorage', 'Des Moines'})
        self.assertEqual(self.client.get('/api/travel/places').json['data']['cityVisits'], {})
        self.assertEqual(self.post({'action': 'cities', 'visits': {'unknown-id': 'visited'}}).status_code, 400)
        result = self.post({'action': 'cities', 'visits': {cities[0]['id']: 'visited', cities[1]['id']: 'not-visited'}})
        self.assertEqual(result.status_code, 200)
        self.assertEqual(len(result.json['data']['cityVisits']), 2)


if __name__ == '__main__':
    unittest.main()
