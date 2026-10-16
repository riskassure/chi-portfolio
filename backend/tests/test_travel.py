import json
from contextlib import closing
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


class TravelTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        app = Flask(__name__); app.register_blueprint(travel.travel_bp)
        self.client = app.test_client()

    def test_key_file_and_missing_key(self):
        key = self.root / 'key.txt'
        with patch.object(travel, 'key_path', return_value=key), patch.dict(os.environ, {'ESRI_BASEMAP_API_KEY': ''}):
            self.assertEqual(self.client.get('/api/travel/config').status_code, 503)
            key.write_text('\ufeffdummy-basemap-key\n', encoding='utf-8')
            response = self.client.get('/api/travel/config')
            self.assertEqual(response.json, {'apiKey': 'dummy-basemap-key'})
            self.assertEqual(response.headers['Cache-Control'], 'no-store')
            key.write_text('key with spaces', encoding='utf-8')
            self.assertEqual(self.client.get('/api/travel/config').status_code, 503)

    def test_coordinates_and_read_only_catalog(self):
        db = self.root / 'photos.db'
        with closing(sqlite3.connect(db)) as conn:
            conn.execute('CREATE TABLE photography_catalog(image_id,file_path,title,location_name,latitude,longitude)')
            conn.executemany('INSERT INTO photography_catalog VALUES (?,?,?,?,?,?)', [
                (1, 'images/photography/valid.webp', '<test>', 'Park', 40, -100),
                (2, 'images/photography/unknown.webp', 'Unknown', '', 0, 0),
                (3, '../../private.txt', 'Unsafe path', '', 40, -100),
                (4, 'images/photography/bad.webp', 'Bad', '', 95, -100)])
            conn.commit()
        before = db.read_bytes()
        with patch.object(travel, 'DB_PATH', db):
            photos = self.client.get('/api/travel/photos').json['photos']
            self.assertEqual([p['image_id'] for p in photos], [1, 2, 4])
            self.assertEqual([p['located'] for p in photos], [True, False, False])
            self.assertIsNone(photos[1]['latitude'])
        self.assertEqual(before, db.read_bytes())
        with patch.object(travel, 'DB_PATH', self.root / 'missing.db'):
            self.assertEqual(self.client.get('/api/travel/photos').status_code, 503)
            self.assertFalse((self.root / 'missing.db').exists())
        for pair in [(None, 1), (float('inf'), 1), (0, 0), (1, 181)]:
            self.assertFalse(travel.located(*pair))
        self.assertTrue(travel.located(0, 15))

    def test_reference_history(self):
        source = Path(__file__).resolve().parents[2] / 'frontend/geography/reference-data.js'
        data = json.loads(source.read_text(encoding='utf-8').split('window.TRAVEL_REFERENCE = ', 1)[1].rstrip(';\n'))
        self.assertEqual(len(data['places']), 51)
        ids = {p['id'] for p in data['places']}
        self.assertEqual(len(ids), 51)
        self.assertTrue({'park-neri', 'park-hale', 'park-havo', 'park-yell'} <= ids)
        self.assertFalse({'park-glac', 'park-isro', 'park-viis', 'park-npsa', 'park-dena', 'park-wotr'} & ids)
        states = {f['properties']['code'] for f in data['states']}
        self.assertEqual(len(states - {'AK', 'ID'}), 48)
        self.assertIn('HI', states)
        countries = {f['properties']['code'] for f in data['countries']}
        self.assertEqual(countries, {'USA', 'TWN', 'CHN', 'VNM', 'FRA', 'CHE', 'DEU', 'GBR', 'ITA', 'CAN'})


if __name__ == '__main__':
    unittest.main()
