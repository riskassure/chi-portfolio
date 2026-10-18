# Website admin runbook

Documentation baseline: 2026-10-17. Checked against the repository's helper menu,
configuration, travel documentation, and Spotify worker. Production details below
are recorded from the deployment in this session, not a new live audit.

## Start here

- Public website: https://www.cwoo.me/
- Local project: `C:\Development\chi-portfolio`
- Local preview: http://127.0.0.1:5001/admin_dashboard.html
- Hosting: PythonAnywhere account `cwoo`, Python 3.13.
- Git saves code history. **Committing and pushing does not deploy the site.**
- Local saves do not generally publish content. Follow the matching workflow below.

Open PowerShell in the project directory and start the helper:

```powershell
python backend/website_workflow.py
```

Use the configured project Python if the installed `python` lacks dependencies.
Do not reinstall dependencies or reset passwords merely to work around an unclear
error. The project's `.venv313\Scripts\python.exe` is another configured runtime;
check that it runs before using it. Production uses its own virtual environment.

Choose **6** to start the local server with the helper's working database. Keep
that terminal open. Use another terminal for the helper while previewing. Sign in
with the local website admin password, which is separate from hosting and Spotify
passwords. Stop the server with Ctrl+C. Run only one local preview server.
After helper code changes, exit and reopen the helper to load the new version.

## Where information lives

| Item | Authoritative location / role |
| --- | --- |
| Published database content | `/home/cwoo/chi-portfolio/backend/portfolio.db` on PythonAnywhere |
| Local working database | Path shown by the helper, saved in `dist/math-workflow.json` |
| Baseline database | Unchanged comparison snapshot recorded by the helper; never edit it |
| Code and reviewed file-based content | Repository; deployed copies must be published separately |
| Saved travel pins, photo map bindings, cities and regions | `frontend/geography/places-data.js` |
| Initial travel defaults | `frontend/geography/travel-data.js` |
| Gallery display count | `frontend/photography/gallery-settings.js` |
| Spotify refresh bookkeeping | `/home/cwoo/.config/chi-portfolio/spotify-top-jobs.db` |
| Local place search cache | `dist/place-search-cache.db` |

There is one main production content database and one small Spotify job database.
Photos and map geometry are files, not additional content databases. Local working
copies, review databases and backups are not independent live data sources.
Do not assume `backend/portfolio.db` is the database currently used by the local
preview: the helper explicitly selects a working copy.

## Publish a reviewed change

1. Edit and verify locally.
2. Choose the preparation option in the table below.
3. Read the proposed differences. **3** stages the reviewed package.
4. **4** checks the current live target for conflicts without applying it.
5. **5**, then `PUBLISH`, applies it with a backup and repeated conflict checks.
6. Verify the affected public page, including its logged-out appearance.

| Change | Preparation option |
| --- | --- |
| Supported math changes | **1** lists math changes; **2** prepares one |
| Biography or resume text | **9** |
| Import Google Photos locally | **10** opens the local import screen; import alone does not publish |
| New local photo | **11** |
| Existing photo title, location or coordinates | **12** |
| Remove photo from gallery | **13**; image file remains accessible at its direct URL |
| Frontend HTML, CSS or JavaScript | **14**; paths relative to `frontend` |
| Backend Python plus matching frontend files | **15**; repository-relative paths |
| Saved gallery display count | **18** |

Option **1** is not a comprehensive list of all website changes. Option **15**
reloads the app and verifies the homepage, but that does not replace checking the
changed feature. It does not install dependencies or run database migrations.
Option **16** retries code reload/verification after a published code package.
Option **17** uploads only the saved Esri key; it is not a general file uploader.
Option **7** changes baseline/working paths and is not a routine publishing step.

If a check reports a conflict, stop that publication and compare the newer live
content. Do not force an older package through. If files already match live, no
new package may be needed. Large reviews are saved as `review.txt` beside the
package under `dist/math-workflow/`; share the relevant section, not credentials.

## Bring database changes home

After publishing database content, verify the live page, stop the local server,
choose **8**, and type `STOPPED` only after it is stopped. This downloads a
consistent live snapshot and compares local changes before selecting a new working
copy. Read the comparison report if it refuses to switch. Restart with **6**.

Old copies and review packages are retained. Option 8 also verifies gallery images
and downloads missing photos. It does not synchronize website code, private
credentials, or all other media. File-only travel or styling changes do not require
option 8. Never replace the entire live database with a laptop copy.

## Travel and photography

On the local map, sign in as admin, search a place name or choose a point on the
map, review its position, and save locally. Photo pin placement can supply a map
name and location without overwriting the original photo catalog metadata.
State/Canadian region selections mean overnight stays; country outlines mean visits.

Publish saved map edits with **14**, selecting `geography/places-data.js`, then
3/4/5. City checklist and region edits use that same file. Photo catalog edits use
12 instead. Changing catalog coordinates/location can invalidate an older photo
map binding; verify its map link afterward. Publish gallery count using 18.
See [travel details](../TRAVEL_MAP.md) for reference-data generation and restrictions;
its original photo counts and first-deployment narrative are historical.

## Spotify automatic refresh

Recorded deployment on 2026-10-17:

- Production manual refresh succeeded with 50 tracks; public browser verified.
- PythonAnywhere scheduled task **1550031** enabled daily at **16:30 UTC**
  (9:30 a.m. Pacific daylight time / 8:30 a.m. standard time).
- Task expiry was reported as null at creation.
- The old Windows task `Chi Portfolio Spotify Refresh` was disabled.
- Verified on October 18: the October 17 scheduled run started at 16:30:15 UTC,
  published 50 tracks at 16:30:29 UTC, and completed at 16:30:30 UTC with exit
  code 0. The public music API timestamp matched. The daily task remains enabled.

No button or running laptop is needed. Visitors receive the saved ranking on page
load/reload; an already open page does not necessarily update itself. Spotify's
six-month top tracks are an affinity ranking, not exact play counts. Errors retain
the last successful list. Editorial overrides and original catalog rows remain.

To check automation, open PythonAnywhere's Tasks page, find the Spotify command,
check it is enabled, and inspect its latest log for a successful refresh and time.
Compare the public music page's Updated date. A date alone does not prove the task
ran, because a manual refresh changes it too. Record the verification result here.

Scheduled command (already configured; do not create a duplicate):

```bash
cd /home/cwoo/chi-portfolio/backend/src && SPOTIFY_TOKEN_PATH=/home/cwoo/.config/chi-portfolio/spotify-tokens.json /home/cwoo/.virtualenvs/chi-portfolio/bin/python -m services.music.spotify_top --database /home/cwoo/chi-portfolio/backend/portfolio.db --refresh
```

If it fails, read the safe error message before retrying. Rate-limit backoff still
applies to forced refresh. Reauthorization may eventually be needed. Local setup
uses `http://127.0.0.1:5001/api/music/spotify/connect`. The exact registered redirect
URI is `http://127.0.0.1:5001/api/music/spotify/callback`.
Credentials transferred to production should not also drive a
local scheduled refresh; do not re-enable the old laptop job. Coordinate a separate
local authorization if continued local refreshing is needed.

There is currently no Spotify credential-upload option in the helper. Renewal
requires a deliberate private transfer and production verification; option 17 is
Esri-only. See [Spotify implementation and setup](../backend/src/services/music/README.md).

## Credentials and renewals

Record locations, never credential values, in documentation or Git.

| Credential | Location |
| --- | --- |
| Local admin password | `%USERPROFILE%\.config\chi-portfolio\local-admin-password.dpapi` (Windows account encryption) |
| PythonAnywhere API settings | `%USERPROFILE%\.config\chi-portfolio\pythonanywhere-api.json` |
| Production hosting settings | `/home/cwoo/.config/chi-portfolio/hosting.json` |
| Esri key | `.config/chi-portfolio/esri-api-key.txt` under each account's home |
| Local Spotify tokens by default | `%LOCALAPPDATA%\chi-portfolio\spotify-tokens.json` |
| Production Spotify tokens | `/home/cwoo/.config/chi-portfolio/spotify-tokens.json` |

Spotify token location can be overridden by `SPOTIFY_TOKEN_PATH`. Keep tokens out
of screenshots, command arguments, deployment packages and logs. Esri's browser
key is intentionally delivered to the map but must retain restricted privileges
and referrers. Its recorded expiration is **October 13, 2027**; rotate before then.
Changing Esri referrers can require regenerating its key. Do not reset working
credentials without understanding which environment uses them.

## Backups, failures and recovery

Publication receipts and reviews live under `dist/math-workflow/`. Server backups
are under `/home/cwoo/backups/`; receipt output identifies the relevant backup.
The initial Spotify refresh backup was
`before-spotify-top-20261017T155529Z.db`. Keep backups private.

- Page looks unchanged: hard-refresh (Ctrl+F5), confirm production URL, and inspect
  the publication result. A Git push alone is not deployment.
- Code uploaded but reload failed: inspect the saved deployment status and hosting
  error log; use option 16 for the verified package when appropriate.
- Local edits would be lost during option 8: retain existing copies and inspect
  its comparison report before resolving differences.
- Spotify authorization expired/mismatched: start a fresh connection in the same
  browser; finish within ten minutes and keep the local server running.
- Failed code release: restore only the changed code from its reviewed backup,
  then reload and verify; preserve current database content.
- Database recovery: preserve the current state and plan the restore first.
  Restoring a full database discards subsequent edits. Never replace an open
  SQLite database or blindly copy an entire old site over production.

No retention policy is agreed yet. Inventory and choose retention before deleting
old databases, media, staging packages, reports or credentials. Some `dist` files
are active workflow state, not disposable build output.

The July 28 pre-macro-backfill snapshot is preserved under
`%USERPROFILE%\.config\chi-portfolio\backups\historical\`, with checksum and
provenance metadata. Its original local copy remains in `backend/backups/`,
ignored rather than tracked in new commits. See the [backup review](BACKUP_REVIEW.md).
This is an archive on the same computer, not an off-device backup.

## Documentation and maintenance workflow

This is the operational starting point. Check code and current receipts when a
statement is uncertain; explicitly record disagreements instead of guessing.
Update this guide in the same change as a workflow change. Keep historical guides
for context, but do not use first-install instructions on an existing deployment.

Further references:

- [Documentation index](README.md)
- [Maintenance assessment plan](MAINTENANCE_PLAN.md)
- [Math synchronization](../MATH_SYNC.md)
- [Broader deployment and recovery details](../UPDATING_WEBSITE.md) (older manual package workflow)
- [First hosting installation](../PYTHONANYWHERE.md) (not a routine update procedure)

This baseline does not certify backup restoration, every page/editor workflow, or
future automatic Spotify runs. These need explicit checks when scheduled, rather
than being inferred from code inspection.

## Maintenance deployment: October 18, 2026

Published Spotify module separation (`dee75b4`) and shared file persistence
(`ca8b81f`) together: six Python files, backed up before publication. Reload and
homepage verification succeeded. Public music, photography and map APIs passed,
and their pages loaded without JavaScript errors. Music still reports 50 tracks.
No live editor writes, database migration or schedule changes were performed.

- Receipt: `dist/math-workflow/d17d34222a09427cbbc981c7134632d8/receipt-b805e43f396a4451861c2e75ced4b831.json`.
- Backup: `/home/cwoo/backups/before-code-update-7f801c82bbf544d084658e0df557fecf`.

## Explicit local directory setup

Importing configuration no longer creates data folders. If preparing an empty
local workspace for imports, run `python backend/src/config.py` from the repository
root. This creates missing standard data/output directories only; it does not
create a database or download content. Existing previews normally need no extra
step. Playlist processing and photo conversion handle their own required folders.
Do not run setup merely to conceal a missing database or configuration error.

## Configuration deployment: October 18, 2026

Published commit `387773b`: config.py and the playlist/photo utilities. Backup,
publication and reload succeeded. Music, photography and map browser checks passed
without JavaScript errors; their APIs plus math search/classifications and session
checks returned HTTP 200. No imports, setup commands or editor writes were run
on production during verification. Database content and schedules were unchanged.

- Receipt: `dist/math-workflow/f25e5c73bcc9411a95f7fb71cb7e577d/receipt-3cf49dc82861479e938a5eedefcb93e3.json`.
- Server backup: `/home/cwoo/backups/before-code-update-edea48d26fb54796a66f662e10b22408`.
