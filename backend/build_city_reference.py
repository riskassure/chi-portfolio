"""Build a curated US city review list with Natural Earth reference points.

This is a travel checklist of major cities, capitals and regional destinations,
not a population ranking. No city is marked visited by this script.
"""
import json
from pathlib import Path
from urllib.request import urlopen
import re

SELECTION = '''Alabama:Birmingham|Huntsville|Mobile|Montgomery
Alaska:Anchorage|Fairbanks|Juneau
Arizona:Phoenix|Tucson|Flagstaff
Arkansas:Little Rock
California:Los Angeles|San Diego|San Jose|San Francisco|Sacramento|Fresno|Oakland|Riverside|Bakersfield|Palm Springs
Colorado:Denver|Colorado Springs|Boulder|Fort Collins
Connecticut:Hartford|New Haven|Bridgeport
Delaware:Wilmington|Dover
District of Columbia:Washington, D.C.
Florida:Jacksonville|Miami|Tampa|Orlando|Tallahassee|Pensacola|Sarasota|Fort Lauderdale|Key West
Georgia:Atlanta|Savannah|Augusta
Hawaii:Honolulu
Idaho:Boise
Illinois:Chicago|Springfield|Peoria
Indiana:Indianapolis|Fort Wayne|South Bend
Iowa:Des Moines|Cedar Rapids
Kansas:Wichita|Topeka
Kentucky:Louisville|Lexington
Louisiana:New Orleans|Baton Rouge|Shreveport
Maine:Portland|Bangor
Maryland:Baltimore|Annapolis
Massachusetts:Boston|Worcester|Springfield
Michigan:Detroit|Grand Rapids|Lansing
Minnesota:Minneapolis|Saint Paul|Duluth
Mississippi:Jackson|Biloxi
Missouri:Kansas City|Saint Louis|Springfield
Montana:Billings|Missoula|Bozeman|Helena
Nebraska:Omaha|Lincoln
Nevada:Las Vegas|Reno
New Hampshire:Manchester|Concord
New Jersey:Newark|Trenton|Atlantic City
New Mexico:Albuquerque|Santa Fe
New York:New York|Buffalo|Rochester|Syracuse|Albany
North Carolina:Charlotte|Raleigh|Greensboro|Asheville|Wilmington
North Dakota:Fargo|Bismarck
Ohio:Columbus|Cleveland|Cincinnati|Toledo|Dayton|Akron
Oklahoma:Oklahoma City|Tulsa
Oregon:Portland|Eugene|Salem|Bend
Pennsylvania:Philadelphia|Pittsburgh|Harrisburg|Erie
Rhode Island:Providence
South Carolina:Charleston|Columbia|Greenville
South Dakota:Sioux Falls|Rapid City
Tennessee:Nashville|Memphis|Knoxville|Chattanooga
Texas:Houston|San Antonio|Dallas|Austin|Fort Worth|El Paso|Corpus Christi|Lubbock|Amarillo
Utah:Salt Lake City|Provo
Vermont:Burlington|Montpelier
Virginia:Richmond|Virginia Beach|Norfolk|Roanoke
Washington:Seattle|Spokane|Tacoma|Olympia
West Virginia:Charleston|Huntington
Wisconsin:Milwaukee|Madison|Green Bay
Wyoming:Cheyenne|Casper'''


def normalized(value):
    return re.sub(r'[^a-z]', '', value.lower().replace('saint', 'st'))


def build():
    root = Path(__file__).resolve().parents[1]
    cache = root / 'dist/us-city-reference.json'
    if cache.exists():
        features = json.loads(cache.read_text())
    else:
        with urlopen('https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_populated_places.geojson', timeout=60) as response:
            features = json.load(response)['features']
    lookup = {(normalized(f['properties']['NAME']), f['properties']['ADM1NAME']): f for f in features if f['properties']['ADM0_A3'] == 'USA'}
    cities = []; missing = []
    for row in SELECTION.splitlines():
        state, names = row.split(':')
        for name in names.split('|'):
            f = lookup.get((normalized(name), state))
            if (name, state) == ('Fort Worth', 'Texas'):
                # Census ACS26 incorporated-place internal point (GEOID 4827000).
                cities.append({'id': 'city-census-4827000', 'name': name, 'state': state, 'latitude': 32.7819538, 'longitude': -97.3485732, 'previouslyExcluded': False})
                continue
            if not f:
                missing.append((name, state)); continue
            p = f['properties']
            cities.append({'id': 'city-' + str(p['NE_ID']), 'name': name, 'state': state,
                           'latitude': p['LATITUDE'], 'longitude': p['LONGITUDE'],
                           'previouslyExcluded': name in {'Nashville', 'Boise', 'Anchorage', 'Des Moines'}})
    if missing:
        raise ValueError('Resolve city names before building: ' + str(missing))
    cities.sort(key=lambda c: (c['state'], c['name']))
    (root / 'frontend/geography/city-reference.js').write_text('window.TRAVEL_CITIES = ' + json.dumps(cities, indent=2) + ';\n', encoding='utf-8')
    print('Wrote', len(cities), 'candidate cities; none marked visited.')


if __name__ == '__main__':
    build()
