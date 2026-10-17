from contextlib import closing
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from flask import Flask

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from services import place_search
from routes import travel


class PlaceSearchTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        for p in [patch.object(place_search, 'cache_path', return_value=Path(temp.name)/'cache.db'),
                  patch.object(place_search, 'NEXT_REQUEST', 0),
                  patch.dict(os.environ, {'PORTFOLIO_PLACE_SEARCH_URL': 'https://nominatim.openstreetmap.org/search',
                                          'FLASK_ENV': 'development', 'PORTFOLIO_LOCAL_PORT': '5001'})]:
            p.start(); self.addCleanup(p.stop)

    def test_results_cache_and_rate_limit(self):
        rows = [{'display_name': 'London, England, United Kingdom', 'lat': '51.5', 'lon': '-0.12'},
                {'display_name': 'Invalid', 'lat': 'nan', 'lon': '1'}]
        with patch.object(place_search, 'urlopen', return_value=io.BytesIO(json.dumps(rows).encode())) as network:
            result = place_search.search('London, UK')
            self.assertEqual(result, [{'name': rows[0]['display_name'], 'latitude': 51.5, 'longitude': -0.12}])
            self.assertEqual(place_search.search('london, UK'), result)
            network.assert_called_once()
            self.assertIn('ChiPortfolio', network.call_args.args[0].get_header('User-agent'))
            with self.assertRaises(RuntimeError): place_search.search('Paris, France')

    def test_bad_input_and_upstream_failure(self):
        with patch.object(place_search, 'urlopen', side_effect=OSError('private upstream details')) as network:
            for query in [None, '', 'x', 'x'*201]:
                with self.assertRaises(ValueError): place_search.search(query)
            network.assert_not_called()
            with self.assertRaises(RuntimeError) as error: place_search.search('London')
            self.assertNotIn('private upstream', str(error.exception))

    def test_only_local_admin_same_origin_can_search(self):
        app=Flask(__name__); app.secret_key='test'; app.register_blueprint(travel.travel_bp)
        client=app.test_client(); origin='http://127.0.0.1:5001'
        with patch.object(place_search, 'search', return_value=[]) as search:
            def post(headers=None):
                return client.post('/api/travel/search', base_url=origin, headers=headers or {}, json={'query':'London'})
            self.assertEqual(post({'Origin':origin}).status_code,403)
            with client.session_transaction(base_url=origin) as session: session['is_admin']=True
            self.assertEqual(post().status_code,403)
            with patch.dict(os.environ, {'FLASK_ENV':'production'}):
                self.assertEqual(post({'Origin':origin}).status_code,403)
            search.assert_not_called()
            self.assertEqual(post({'Origin':origin}).json,{'results':[]})


if __name__ == '__main__': unittest.main()
