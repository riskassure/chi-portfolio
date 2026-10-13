# Photography services

## Organization

- `google_photos_auth.py`: OAuth authorization, token refresh, private credential paths.
- `google_photos_import.py`: Picker requests, private drafts, image conversion, publication.
- `../../routes/google_photos.py`: HTTP endpoints for the connection and import workflow.
- `../../templates/photography/`: review-page HTML.
- `../../static/photography/`: review-page JavaScript and CSS.
- `../../../../frontend/photography/`: public gallery page and admin controls.

This follows the existing `services/math` and `services/music` layout. Public
URLs and private credential, token, draft, and photo locations are independent
of this source-code organization.

## Local Google Photos connection

Start the backend using option 6 in `backend/website_workflow.py` so the selected
working database and saved admin password are used.
Open the photography page through your local frontend server, sign in as the
portfolio administrator, and click **Connect Google Photos**. Alternatively,
open http://127.0.0.1:5001/api/photography/google/connect directly; it includes
a portfolio admin login when needed. Click **Continue to Google**, choose the
Google account registered as a test user, and grant the Picker permission.

Credentials default to `~/.config/chi-portfolio/google-oauth.json`.
`GOOGLE_PHOTOS_CREDENTIALS` can override this path, which must remain outside
the repository. Add the callback in Google Cloud for the existing OAuth web
client, then download its updated JSON to the same private credential path.
Keep any existing callback addresses. The registered redirect URI must be exactly
`http://127.0.0.1:5001/auth/google/callback`.

Access and refresh tokens are saved outside the repository at
`%LOCALAPPDATA%/chi-portfolio/google-photos-tokens.json` on Windows. Never commit
or serve this file. Google may require reconnection when test authorizations
expire or access is revoked. The backend supports refreshing access tokens.

After connecting, open http://127.0.0.1:5001/api/photography/google/manage
or click **Add from Google Photos** in the photography admin controls.
Select photos and click Done in Google's picker. Keep the review tab open
while photos import. If popups are blocked, use the selection link on the page.
Failed imports can be retried; already imported photo content is skipped.
Videos are skipped. Photos are resized to fit 1920 by 1920 and saved as WebP.

Draft images live in `%LOCALAPPDATA%/chi-portfolio/google-photo-drafts`, outside
the website folder, with metadata in the `google_photo_drafts` database table.
Edit a title or location and click **Add to local gallery** on each desired photo.
You can also review all drafts and use **Add all reviewed drafts to local gallery**.
This never publishes to PythonAnywhere. Adding locally copies the image into `frontend/images/photography` and inserts a
visible catalog entry, eligible for the existing gallery rotation. Refresh the
gallery to see newly published photos. Drafts survive browser/backend restarts;
unfinished Google selections may require retrying or starting a new selection.

The integration is restricted
to the loopback backend and is disabled when `FLASK_ENV=production`. Deployment
requires separate host, HTTPS, storage and authentication configuration.

Tests: `python -m unittest discover -s backend/tests -p "test_google_photos*.py"`
Tests use fake credentials and mocked Google responses; real consent must be
completed in the account owner's browser.

References:
- https://developers.google.com/identity/protocols/oauth2/web-server
- https://developers.google.com/photos/picker/guides/sessions

## Publishing a new photo to PythonAnywhere

Use helper option 11 after adding the photo locally. Select one new gallery
photo and review its image, title, location and visibility locally. Then use
3 (stage), 4 (live check), and 5 (explicit publish). The package includes the
WebP and metadata. No Google credentials, tokens or private drafts are uploaded.

The publisher verifies checksums, refuses existing conflicting images or rows,
backs up the live database, creates the image without overwriting files, then
inserts and verifies the catalog row. Repeat publication is skipped when image
and metadata match. A failed database write may leave a verified image without
a catalog row; retry after live preflight can reuse it. A dropped connection
requires checking live before retrying. Publication supports new photos only;
publishing existing-photo edits and deletions is not yet supported.

After checking the public gallery, stop the local server and use option 8.
It compares photo metadata by filename, checks every live gallery image's
SHA-256, and downloads missing WebP files without overwriting local files.
Local import drafts are retained in the new working database and their gallery
IDs are remapped by filename. The new baseline is an unchanged live snapshot.
Unpublished local photos, conflicting image bytes or metadata, and remote-only
private drafts stop for review. Existing databases and unlisted local image
files are preserved. Website source files and other media are outside this step.
