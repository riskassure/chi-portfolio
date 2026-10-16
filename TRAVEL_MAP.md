# Travel map

Preview using website helper option 6, then open
`http://127.0.0.1:5001/geography/index.html`.

The Esri Maps SDK is pinned to 5.1. The basemap uses only the Basemap styles
service privilege. The public `/api/travel/config` endpoint reads
`~/.config/chi-portfolio/esri-api-key.txt` (UTF-8, key only), or the
`ESRI_BASEMAP_API_KEY` environment variable. Missing configuration returns 503.
The key is intentionally available to the browser; it is not a privileged
server secret. Restrict its referrers to the production origin and the two
local origins. Never configure private/all-owner ArcGIS credentials here.
Keep the value out of Git, diagnostics, screenshots, and deployment packages.
The current credential expires October 13, 2027; rotate it before expiration.

## Travel history and reference data

`frontend/geography/travel-data.js` contains the confirmed overnight-state
exceptions, country codes, and an additionalPlaces array for individually
confirmed places. Additional places use `{id, name, kind: 'place', latitude,
longitude}`. Major cities have deliberately not been inferred.

`reference-data.js` contains boundary geometries and the 51 visited park
reference points. Rebuild explicitly with
`.\.venv313\Scripts\python.exe backend/build_travel_reference.py` (network needed).
The builder checks counts and rejects incomplete reference downloads. This is
a static reviewed snapshot, not a runtime dependency on remote feature layers.

Sources retrieved October 14, 2026:
- [Natural Earth public-domain terms](https://www.naturalearthdata.com/about/terms-of-use/)
- [Natural Earth 1:50m GeoJSON source](https://github.com/nvkelso/natural-earth-vector/tree/master/geojson)
- [NPS boundaries](https://services1.arcgis.com/fBc8EJBxQRMcHlei/ArcGIS/rest/services/National_Park_Service_Boundaries/FeatureServer/0)
- [NPS national park list](https://www.nps.gov/aboutus/national-park-system.htm)
- [Esri SDK configuration](https://developers.arcgis.com/javascript/latest/references/core/config/)

Park points are boundary centroids, not entrances, trailheads, or exact visit
coordinates. New River Gorge's older source label is updated to its current
designation. Exclude Alaska parks, Glacier, Isle Royale, Virgin Islands,
American Samoa, and Wolf Trap (not one of the 63 designated national parks).
States are filled except Idaho/Alaska; Hawaii is included. Taiwan is a separate
visited feature. Natural Earth boundaries are generalized cartographic data.

## Photography

The read-only `/api/travel/photos` endpoint reads the selected working database.
Only valid finite coordinates within bounds become pins; the existing `(0,0)`
placeholder is omitted. Photos sharing coordinates rounded to five decimal
places share one pin. Reviewed named-location references now provide general
locations for the 14 named photos (13 points). These are labeled as general
city/park/trail locations, not exact camera positions. Their source URLs are
stored alongside the aliases in `places-data.js`. Four photos still have
unknown location text and need owner placement. Glade Creek Grist Mill at
Babcock was explicitly confirmed by the owner. Arbitrary new names are not
automatically geocoded.

Photo locations with valid coordinates link to
`geography/index.html?photo=<encoded-file-path>`. Pins show photo thumbnails
linking back to an individual photograph, including one outside the current
gallery rotation. The individual view does not auto-rotate. Removed catalog
rows are excluded. No schema changes or catalog writes occur in map routes.
Existing photo detail editing and publication can be used to confirm coordinates.

## Local editor and city checklist

Sign in through the local admin dashboard, then open the map. The editor can
add, rename, move, and remove custom visited places. Choose a point by clicking
the map or enter coordinates. Selecting a photo shows its thumbnail and lets
the editor position its pin. On the photography page, map links are present in
both editor and visitor modes; unresolved photos have a local editor action
“Place this photo on the map.” After saving, that action becomes a location link.

Map edits save atomically into `frontend/geography/places-data.js`. The API
requires local loopback access, a signed-in admin, a matching Origin, and an
unchanged file revision. Production edits are rejected. A file lock prevents
concurrent map writes. Existing photo title/location/coordinate columns are
not overwritten by pin placement. Photo pin overrides are bound to file path
and expected catalog location text/coordinates; editing those catalog fields
invalidates an older override. Gallery rotation does not affect bindings.
Removed catalog photos never get resurrected by map bindings.

`geography/cities.html` provides 159 candidate cities grouped by state. This is
a curated travel checklist, not a population ranking. Natural Earth supplies
city reference points; Fort Worth uses the Census ACS26 internal point.
Nashville, Boise, Anchorage and Des Moines default to not visited; no other
city is marked visited without an explicit review/save. “Mark remaining cities
visited” requires confirmation and preserves not-visited/unsure choices even
when a search filter hides them. Visited cities use an Esri clustered point
layer. Clicking a cluster zooms in. City choices never modify overnight-state
or country shading. A text checklist can also be downloaded from the page.
Rebuild the candidate list with `python backend/build_city_reference.py`.

The map editor writes only source data, so option 8's database refresh preserves
these edits. To publish subsequent map changes, review and publish
`geography/places-data.js` with helper option 14. Photo metadata changes still
use the separate existing photo review/publication workflow.

## Publication

This is a local preview until reviewed. The site helper's code publication
supports the new Python route, app registration, and HTML/CSS/JS files together.
The generated reference data is JavaScript to fit that existing file workflow.
The private Esri key must also be installed separately on PythonAnywhere at the
same home-relative path (or environment variable), with matching referrers.
Reload is needed for the Python routes. Option 8 does not copy source files or
private credentials. No database migration is required.

## Visited regions

The local admin map panel includes searchable checklists for all 50 U.S. states,
13 Canadian provinces and territories, and Natural Earth countries and territories.
States and Canadian regions represent overnight stays; country outlines represent
visits. Existing data defaults to 48 states (except Idaho and Alaska), no Canadian
regions, and the original ten countries. Saved empty selections stay empty.
Region edits share the atomic revision-checked places-data.js workflow and preserve
photo locations, custom places and city decisions. Country outlines use a thinner
1-point stroke. Canadian regions use the same green fill as states.

The boundary builder also produces country-reference.js (world outlines, rounded
to four decimal places) and region-reference.js (editor labels and identifiers).
These are required alongside reference-data.js, and each remains under the
publication helper's 2 MiB per-file limit.

## Esri key upload helper

Choose option 17 to upload the key already saved in your local
`~/.config/chi-portfolio/esri-api-key.txt` to the same home-relative path on
PythonAnywhere. SSH may ask for the hosting account password. The key travels
through SSH standard input, never in command arguments or deployment packages.
The helper validates it, writes a temporary owner-only file, atomically replaces
the destination, and verifies the saved bytes without displaying them. It does
not publish website code or reload the app. A successful upload prepares the
first map deployment; then use option 15 and the normal stage/check/publish flow.

## Gallery display count

The photography page saves its 3/6/9/12-photo preference locally in
`frontend/photography/gallery-settings.js`. The initial saved count is 12,
matching the local gallery. Only a signed-in local editor can save the setting;
stale revisions are rejected. Visitors read the preferred number of photos,
prioritizing the database's current rotation and filling from the remaining
catalog without database writes. Rotation also uses the saved count, ignoring
stale browser limits. Local and live rotations may still select different photos.

For the first release of this feature, use helper option 15 with:
`backend/src/services/gallery_settings.py, backend/src/routes/admin_photography.py, frontend/photography/gallery-settings.js, frontend/photography/gallery.js`.
Review, stage, check live, and publish/reload as usual. After that first release,
option 18 prepares only the saved display settings for the normal 3/4/5 workflow.
Changing the local count alone does not change production.
