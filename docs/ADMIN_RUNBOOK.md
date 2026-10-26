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
- New to web programming? Read [How the website works](administration/HOW_THE_SITE_WORKS.md)
  first: what runs in the browser and what on the server, when a reload is needed,
  browser caching, logins, and where errors show up.

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
The same goes for the local server: after a `git pull` or an edit that changes
Python under `backend/src`, stop it and start **6** again. Frontend files (HTML, CSS,
JavaScript) are read fresh on each page load, so Ctrl+F5 in the browser is enough.

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
| Several new math entries at once | **20** publishes a reviewed batch of new entries; see [Publish a batch of new entries](administration/deployment/CONTENT_SYNC.md#publish-a-batch-of-new-entries) |
| Math entry with new, changed or missing PSTricks diagrams | **19** renders missing SVGs on this computer, then **1** and **2**; see [Publish a diagram change](administration/deployment/CONTENT_SYNC.md#publish-a-diagram-change) |
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

## Add a mathematics entry

Follow [Adding a math entry](features/math/ADDING_ENTRIES.md) for field guidance,
previewing, local saving and publication. Start with helper option **6**, sign in
locally, then open `http://127.0.0.1:5001/math/create.html`. Follow the existing
[authoring standards](features/math/AUTHORING_STANDARDS.md) for mathematical prose
and notation. Search for duplicates before creating an entry.

For a new text/equation entry, prepare with **2** and publish via **3/4/5** after
review. PSTricks diagrams are rendered on this computer with **19** and published
with the entry. Included images and other media still need a separate
publication plan, even if local preview works. A Git push does not publish database content. Verify live, then refresh
the baseline/working copy with **8** after stopping the local server.

Alternatively, the guide's **production-first** section explains backing up,
creating the entry directly on the live site, verifying it, and using **8** to
bring it home. A live save is immediately public and does not need helper
publication. Conflicting unpublished local edits must be reconciled before a
refresh can switch working copies. Option 8 is not a general two-way merge. It
downloads missing math diagram SVGs but not source code. Production-first is not
a route for new or changed diagrams or images, because the live editor would
render diagrams on the server. Use the diagram route instead.

## Terms used for math entries

These words have a fixed meaning in the bulk-add and merge procedures below and in
the guides they link to.

| Term | Meaning |
| --- | --- |
| Live | The public site's database on PythonAnywhere. "Publish" means changing live through the helper. |
| Working copy | The laptop database the helper and the local server (option **6**) use. Your local edits go here. |
| Baseline | The unchanged copy of live that option **8** last brought home. Option **1** lists the differences between the working copy and the baseline. Never edit it. |
| Bring home | Option **8**: download a fresh copy of live and install it as the new baseline and working copy, after checking that no unpublished local edit would be lost. |
| Canonical name | An entry's fixed internal name, such as `CompletenessTheoremForPropositionalLogic`. The helper asks for it by this name. It can't be changed after saving and is not always the slug's words capitalised. |
| Slug | The entry's address on the site, such as `completeness-theorem-for-propositional-logic` in `math/concept.html?slug=...`. Fixed after saving. |
| Package | The reviewed file the helper prepares for one change. Options 3, 4 and 5 stage it, check it against live and publish it. |
| Receipt | The record the helper saves after a publish: what changed and which server backup was taken. |
| Batch | A group of new entries published together with option **20**, under a name you give it. |
| Merge | Making two entries that are really the same page into one, with option **21**. Nothing is deleted. |
| Survivor (S) | The entry that stays. It keeps its title, slug, canonical name and URL, and gains the other entry's content. |
| Absorbed entry (A) | The entry merged into the survivor. It is retired, and its old URL shows the survivor with a note. |
| Retire | Mark an entry as no longer active, without deleting it. It disappears from search and lists, and its name and slug stay reserved. A retirement with no survivor shows "This entry has been retired" at its old URL. |
| Merge session | Option **21 → 2**: the helper freezes the live versions of A and S in `dist/merge-sessions/<id>/` before you edit anything, so later checks can prove nothing else changed. |
| Metadata-only merge | A merge in which the survivor's text is left unchanged and only A's names, MSC codes and related links are added to it. |
| Synonym | Another name for the same concept. Synonyms appear in search and are linked automatically in other entries' text. |
| Defined term | A further term defined inside an entry ("Other Concepts Defined Here"). It is also linked automatically. |
| Alias clash | Two active entries sharing a title, synonym or defined term, which makes automatic links ambiguous. A merge refuses to create a new one. |
| Migration | A script in `backend/src/database/math/migrations/` that records in git what was published, so the repository can rebuild it. It does not publish anything. |

## Add many new entries at once (option 20)

This is the route used for the K_1 and naive set theory batches.
Every step is on the laptop, in the project folder. Details, stops and resuming:
[Publish a batch of new entries](administration/deployment/CONTENT_SYNC.md#publish-a-batch-of-new-entries).

1. **Start clean.** `git pull`. Stop the local server, run **8** and make sure it
   switches to a fresh working copy. Then **1** should list nothing: anything it
   lists now is an unpublished edit that will later stop option 8.
2. **Write the entries in the working copy**, either one at a time in the local
   editor (**6**, then `http://127.0.0.1:5001/math/create.html`), or with a script
   run against the working copy while the local server is stopped (preview first,
   then apply with its backup). Follow the [entry guide](features/math/ADDING_ENTRIES.md)
   and the [authoring standards](features/math/AUTHORING_STANDARDS.md). Related
   concepts and `\PMlinkname` targets must be live entries or entries in the same
   batch, and must not form a loop.
3. **Review locally.** Start **6** and read every new page: equations, proofs,
   diagrams, and automatic links that point at the wrong entry. Fix them in the
   working copy. **1** must now list exactly the batch's new entries, none marked
   `[unsupported]` (render missing diagram SVGs with **19**).
4. **Option 20.** Select the entries (`ALL` or `1,3-5`) and name the batch. Fix
   every blocker it reports and choose 20 again. Read
   `dist/math-batches/<batch id>/review.txt`. The publish order is option 20's
   own, so live ids follow that order, not the order you wrote the entries in.
5. **`PUBLISH ALL`.** It publishes one entry at a time with a backup each. If it
   stops, fix the cause and choose 20 again, then `RESUME`. Nothing that is already
   live is published twice.
6. **Check the live pages** listed in `pages-to-check.txt`, logged out, then type
   `VERIFIED`.
7. **Option 8.** Stop the local server, type `STOPPED`. If it reports
   "synchronization blocked", the batch is still published: resolve the named
   difference and choose 20 again (nothing is republished).
8. **Record it in git:** a migration `add_<topic>_entries_<date>.py` built on
   `math_entry_batch.run_batch`, with its `ORDER` list in live id order, checked to
   reproduce the live rows. Open a PR, merge it, then `git pull` on the laptop. See
   [Record a batch in git](administration/deployment/CONTENT_SYNC.md#record-a-batch-in-git).

Edits to existing entries are not part of a batch: publish them one at a time with
**1**, **2**, then 3/4/5, and run **8** once at the end.

## Merge two entries (option 21)

Use this when two entries are really the same page. The absorbed entry **A** is
retired into the survivor **S**; nothing is deleted. One merge at a time, and each
one is brought home with **8** before the next. Full procedure, checks and undo:
[Merging and retiring entries](features/math/MERGING_ENTRIES.md).

1. **Start clean.** `git pull`; stop the local server, run **8**; **1** lists nothing.
   Decide which entry survives (the URL to keep) and find both canonical names (the
   [candidate report](features/math/MERGE_CANDIDATES.md) lists them).
2. **Freeze:** **21 → 2**, `merge`, A's canonical name, S's canonical name, a reason
   (it is shown on A's old page). Do this before editing either entry.
3. **Edit S's text** in the local editor (**6**, `math/edit.html?id=<S's id>`): fold
   in A's content. Change only the body and synonyms; leave A untouched. Check S's
   local page.
4. **Publish S:** **1** shows S; **2** prepares it; then 3, 4, 5. Check S's live page.
   No option 8 is needed yet.
5. **Prepare the merge:** **21 → 3**, pick the session. Title as synonym: `Y`
   (normally). Metadata-only: `N` (you changed S's text). Read the review.
6. **Publish the merge:** 3, 4, 5.
7. **Verify live:** S's page, A's old URL (`math/concept.html?slug=<A's slug>`)
   shows S with the merge note, and a search for A's title shows one entry.
8. **Option 8:** stop the local server, type `STOPPED`. It confirms the merge
   receipt and replays it before comparing.
9. **Record it in git:** a migration from `dist/merge-sessions/<id>/receipt.json`
   (step 8 of the merge guide), then a PR, merge, `git pull`.

Keep `dist/merge-sessions/`: undo (**21 → 4**) needs the session folder. A PR that
touches math readers merges only with `backend/tests/test_retirement_readers.py`
passing.

## Other math entry notes

Option **1** marks any math change that option 2 would refuse as `[unsupported]`
and explains why. Some existing entries cannot be patched through the helper at
all; see [Entries the helper cannot publish](administration/deployment/CONTENT_SYNC.md#entries-the-helper-cannot-publish).

Database-only entry changes do not require a Git commit. Commit/push any related
tracked code or documentation separately; deploy required code before content
that depends on it. The entry guide includes a Git-versus-content checklist.

## Travel and photography

On the local map, sign in as admin, search a place name or choose a point on the
map, review its position, and save locally. Photo pin placement can supply a map
name and location without overwriting the original photo catalog metadata.
State/Canadian region selections mean overnight stays; country outlines mean visits.

Publish saved map edits with **14**, selecting `geography/places-data.js`, then
3/4/5. City checklist and region edits use that same file. Photo catalog edits use
12 instead. Changing catalog coordinates/location can invalidate an older photo
map binding; verify its map link afterward. Publish gallery count using 18.
See [travel details](features/travel/TRAVEL_MAP.md) for reference-data generation and restrictions;
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
Esri-only. See [Spotify implementation and setup](features/music/SPOTIFY.md).

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
key is intentionally delivered to the map: it is sent to every visitor's browser,
so anyone can read it. It is safe only because Esri limits it to map privileges and
to requests whose *referrer* (the page address the browser reports) is this site;
keep those restrictions. Its recorded expiration is **October 13, 2027**; rotate before then.
Changing Esri referrers can require regenerating its key. Do not reset working
credentials without understanding which environment uses them.

## Backups, failures and recovery

See the [October 18 backup review](administration/backups/BACKUP_RECOVERY.md) for inventory and an isolated
database recovery exercise: integrity and five application queries passed on a
temporary copy of the pre-Spotify snapshot. A subsequent full-site archive restore also passed: 18 photos, 76 diagram
references and ten page/API checks. See that review for archive locations and
checksums. Hosting/credential recovery, an additional off-device copy and retention
policy remain follow-up decisions.

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
ignored rather than tracked in new commits. See the [backup review](administration/backups/HISTORICAL_BACKUP_REVIEW.md).
This is an archive on the same computer, not an off-device backup.

## Documentation and maintenance workflow

This is the operational starting point. Check code and current receipts when a
statement is uncertain; explicitly record disagreements instead of guessing.
Update this guide in the same change as a workflow change. Keep historical guides
for context, but do not use first-install instructions on an existing deployment.

Further references:

- [Documentation index](README.md)
- [Maintenance assessment plan](maintenance/MAINTENANCE_PLAN.md)
- [Math synchronization](administration/deployment/CONTENT_SYNC.md)
- [Broader deployment and recovery details](administration/deployment/MANUAL_UPDATES.md) (older manual package workflow)
- [First hosting installation](administration/deployment/PYTHONANYWHERE.md) (not a routine update procedure)

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
