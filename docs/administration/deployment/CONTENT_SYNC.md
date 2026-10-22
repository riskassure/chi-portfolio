# Website content synchronization

For the everyday workflow and environment overview, start with the
[admin runbook](../../ADMIN_RUNBOOK.md). This guide provides detailed helper
procedures. Other guides are listed in the [documentation index](../../README.md).

## Python and matching frontend deployments (options 15 and 16)

Option **15** prepares a reviewed code update. Enter repository-relative paths,
separated by commas, for example:

```text
backend/src/routes/admin_photography.py, frontend/photography/gallery.js
```

The supported scope is Python under `backend/src` plus matching frontend HTML,
CSS and JavaScript. A code package must contain a changed Python file; use option
14 for frontend-only updates. Database migrations, dependency installation,
private settings, WSGI configuration, file deletion and other backend tools are
outside this step. Test the selected changes locally with the installed
dependencies before publication.

Preparation reads live expected files and lists the account's websites. With
one website it selects that domain; otherwise choose one from the list. Review
all differences, then use **3**, **4**, and **5**. Python source is compiled for
syntax validation locally and on the server without executing it during review
or preflight. This is not an import/dependency/runtime test. Matching frontend
and Python changes share the existing batch backups, conflict checks and
file-replacement rollback. Batches are not a site-wide atomic deployment.

Before the `PUBLISH` confirmation, the helper displays the domain it will reload.
After uploading, it verifies that the live files match the package, sends an API
reload request for that account webapp, and checks the public HTTPS homepage.
The private API token is used only with the PythonAnywhere API and is never sent
to the public website. No database refresh is needed for code-only deployment.

The upload receipt and deployment receipt are separate. Deployment states are
`RELOAD_PENDING`, `RELOAD_ACKNOWLEDGED` and `HOMEPAGE_VERIFIED`. HTTP 200 on the
homepage does not prove that every worker or changed feature is healthy: hard
refresh the browser, sign in and test the actual changed feature afterward.
For the photo editor, verify that a title edit saves and survives a page refresh.

If reload or verification fails, the uploaded files and backups remain. Inspect
the live site and PythonAnywhere error log before choosing **16** to retry reload
and homepage verification. Option 16 first rechecks the package's live file
checksums and refuses newer conflicting files. It retains a separate receipt
for each attempt. A failed runtime check does not automatically restore old code
or trigger repeated reloads. Recovery from a runtime failure uses the recorded
file backups, followed by another reload; do not restore an old whole database.

Reload API reference: https://help.pythonanywhere.com/pages/API/

## Publishing frontend files (option 14)

Edit and test HTML, CSS or JavaScript locally first. Choose **14. Prepare frontend
files** and enter up to 20 paths relative to `frontend`, separated by commas,
for example `photography/photography.css`. Blank input cancels. Only UTF-8
`.html`, `.css` and `.js` files are allowed (2 MB per file, 10 MB of review text).
Python, database files, private settings, media, links and deletions are excluded.

The helper reads those exact files from PythonAnywhere over SSH and packages
the live expected content together with your local replacement. Review **all**
differences: this is a freshly captured live version, not a historical common
baseline, and it does not infer which side's edits are newer. Unchanged selected
files are omitted. New files require the live path to be absent.

Use **3** to stage, **4** to check live and **5** to publish after reviewing. A
local edit after preparation invalidates the package. A newer conflicting live
edit stops publication. Matching repeated publication is skipped. No packaged
JavaScript is run by the publisher; these files will run normally in visitors'
browsers after publication.

Publication holds a dedicated lock, verifies backups of all affected existing
files, stages replacements beside their destinations, then replaces each file
individually. The backup folder under `/home/cwoo/backups/before-frontend-update-*`
contains exact `.before` bytes and `manifest.json` with paths, checksums and file
modes. Existing modes are preserved; new public files use mode 0644. A batch is
not a site-wide atomic switch: visitors may briefly see mixed file versions.
Do not edit the selected live files concurrently through another tool.

On an ordinary failure, the publisher attempts to restore files it changed and
verifies them. It refuses to overwrite a concurrent edit during restoration.
An interrupted process or failed recovery may leave `.frontend-publish.lock`
in the backups folder. Check its `backup.txt`, the backup manifest, the live
files and the pending local receipt before recovering; do not simply remove
the lock or rerun. After resolving the live state, the lock can be cleared for
a new reviewed attempt. Backups are retained for recovery.

After success, hard-refresh affected public pages with **Ctrl+F5** and check their
behavior. The upload verifies file bytes, not browser behavior. These frontend
files are served directly, so this step does not reload PythonAnywhere or touch
the database; option 8 is not needed for a file-only update. Option 8 still does
not download website source code.

Option 14 does not deploy Python code or coordinate database migrations.
Only publish frontend changes compatible with the backend already live. In
particular, the newer gallery title editor also needs the updated Python route;
use option 15 to review and deploy both files together.

## Google Photos and new-photo publication

The local launcher configures the Google Photos integration for its chosen port
(normally 5001). Register `http://127.0.0.1:5001/auth/google/callback` on the
existing Google OAuth web client and preserve previous redirect URIs. Include
the same URI in the existing private `~/.config/chi-portfolio/google-oauth.json`
without changing its client ID or secret. Do not place
that JSON in the repository. Google still requires explicit photo selection and
consent; the program handles downloads and WebP conversion afterward.

Start the local server with **6**. From another helper terminal choose **10** to
open the Google Photos review page, or use the photography page's Google links.
Review titles and locations, then add individual drafts or all reviewed drafts
to the local gallery. This does not publish them to the live website.

Choose **11** to prepare one new local gallery photo. Review it, then use **3**,
**4**, and **5** as usual. The package contains both the image and its catalog
metadata, with checksum verification and a live database backup. Existing image
or metadata conflicts stop publication; matching repeats are skipped. Failed
inserts can leave a verified unlisted image for a later retry, but never commit
a catalog entry before its image is verified. After checking the live gallery,
use **8** to refresh the baseline and bring gallery images home. Gallery removal
is supported by option 13; permanent image deletion and image replacement are
not yet supported.

### Removing a photo from the gallery

Choose **13. Prepare removal from the gallery (keep image)** and select an
existing photo. Enter 0 at the photo-number prompt to cancel. Preparation only
creates a review package; it does not remove anything locally or online.
Unpublished local edits to that photo must be resolved first.

Review the filename, title and location, then use **3** (stage), **4** (check
live), and **5** (publish). The publisher repeats the metadata and image-checksum
checks, backs up the live database, and removes only the selected catalog row.
Linked Google Photos drafts are retained with their gallery links cleared.
Rotation changes do not block removal; newer content changes do. Repeating an
already completed removal is a no-op if the retained image still matches.

The image file remains on disk and accessible at its direct URL. This removes
the photo from gallery listings, not from hosting. After checking the live
gallery, stop the local server and use **8** to refresh the local gallery and
baseline. Local private drafts for unchanged removed entries become available
for intentional re-addition; their image files are preserved. Unpublished local
edits to a removed entry still stop synchronization for review.

To abandon a prepared removal, do not publish it; preparing another package
replaces the selected job. Recovery after publication uses the retained image
and database backup. A retained Google Photos draft can also be added locally
again and published as a new photo after refreshing the baseline. Do not restore
an entire old live database over subsequent website changes.

### Updating existing photo details

Start the local server with **6**, sign in as admin, and open the photography
page. Edit the title, location or coordinates and click **Save Details**. Stop
the server, restart the helper if necessary, and choose **12. Prepare changes
to existing photo details**. Select the photo and review the before/after fields,
then use **3**, **4**, and **5** to stage, check and publish it.

This metadata-only package includes the expected baseline values, replacement
values and local image checksum. Live checks require that image and the expected
details still match. Publication repeats the checks under a database write lock,
creates a verified backup and changes only title, location and coordinates.
Image bytes, filenames, gallery IDs, visibility and rotation history are not
changed. Matching repeats are skipped; newer conflicting edits stop publication.
After checking the live gallery, use **8** to refresh the baseline.

The title input is part of the editor update. Publishing metadata does not
deploy its JavaScript or backend route; use option 15 for the paired code files.
The live gallery can display updated titles with its existing code.

## Remembered local admin password (Windows)

Option **6** now asks you to choose and confirm a password only on the first
startup. Later startups reuse it. The encrypted file is
`~/.config/chi-portfolio/local-admin-password.dpapi`, outside the project and Git.
It uses Windows DPAPI current-user protection; software running under your Windows
account can decrypt it. It is separate from the live admin and PythonAnywhere
account passwords. Browser login is still required after a server restart.

To change a forgotten password, stop the local server and run:

```powershell
.\.venv313\Scripts\python.exe backend/start_local.py --reset-password --database PATH-TO-YOUR-WORKING-DB
```

Use the working path shown in the helper. `--session-password` instead chooses a
temporary password without overwriting the saved one (also usable off Windows).
Neither command changes live credentials. Use the normal VS Code terminal, not
PowerShell ISE. Never put passwords in command arguments or Git.

Windows protection reference: https://learn.microsoft.com/en-us/windows/win32/api/dpapi/nf-dpapi-cryptprotectdata

## Biography and resume updates

Use **9. Prepare biography or resume update** in the existing helper. Enter
`bio` or `resume` after editing and saving that page through the local admin UI.
Review the before/after text fields, then use **3** (stage), **4** (live preflight),
and **5** (explicit publication). The remembered baseline and working database
paths are used. No separate paths or upload commands are needed.

The package contains the expected page revision, replacement plain-text fields,
and a fingerprint of the local HTML template. The live template must match and
the expected revision must still be current. Publication creates a verified
database backup and appends a new revision in one transaction, preserving history.
Retired or unknown fields cannot be reintroduced. This transfers admin text edits;
it does not publish HTML layout, links, PDFs, photos, or other files.

After publication verify the page, then use Bring website changes home. Its
comparison ignores profile save timestamps and JSON formatting, but checks all
revision numbers and text fields, including history. Divergent history stops
for review even when the latest visible text matches.

## Guided helper (recommended)

### Bring website changes home (menu option 8)

Stop the local server, then select **8** and type `STOPPED`. The helper downloads
a new verified live snapshot using the existing SSH downloader (which may ask
for the PythonAnywhere account password twice). It compares every database table
against the remembered baseline and working copy, not just math fields.

For ordinary tables, refresh requires that local content is unchanged from the
baseline or matches live (profile save timestamps/JSON spacing are ignored).
Photos are compared individually by filename and editable metadata, including
visibility. Gallery IDs, rotation counters and rotation timestamps may differ.
Unpublished or conflicting local photos still stop the refresh. Unrecognized
schemas and changes to other media-related tables also stop for review.

All gallery WebP files referenced by the live snapshot are checksum-verified
against a read-only SSH manifest. Missing images are downloaded using SCP into
the new sync folder, verified, then installed without overwriting existing files.
A missing remote image, unsafe filename or different local image stops the
refresh. Same-filename image replacements require manual review. Limits are
25 MB per image and 1 GB for the gallery. Files absent from the live catalog are
not deleted locally.

Local Google Photos import drafts are preserved in the new working database;
their gallery links are remapped by filename to the live IDs. Private draft
images stay in their existing local folder. The baseline stays an exact live
snapshot. Remote-only private drafts require review because their private image
files are not part of the gallery download.

On success it creates verified `base.db` and `working.db` in a new ignored
`dist/home-sync/<unique-id>/` folder and remembers those paths. The original
databases, downloaded snapshot, and previous workflow settings are preserved.
Choose **6** to restart the local server on the refreshed working copy. The
baseline must remain unchanged. A comparison report is saved on both successful
and blocked comparisons. No live database writes or reloads are performed.

Website program files and other media (music, PDFs, math diagrams) are not
downloaded. If a transfer or state save fails, the old database paths remain
active; verified extra images may remain and can be reused on retry. The report's
`refresh_complete` flag indicates whether the switch finished. Stop the local server before switching copies
so it does not keep writing to the old database. Do not run concurrent helpers.

```powershell
.\.venv313\Scripts\python.exe backend/website_workflow.py
```

The numbered menu remembers the baseline and working database paths in ignored
`dist/math-workflow.json`. It does not store passwords or API tokens. Choose
Show local changes, then Prepare an entry and review the displayed diff. Next
choose Stage, Check live, and Publish. Publishing requires typing `PUBLISH` and
the transactional publisher still repeats the live checks. SSH may prompt for
your PythonAnywhere account password. The existing private API settings are
used for staging.

Prepared packages, review reports and receipts are retained under ignored
`dist/math-workflow/`. Baseline or package changes and edits to the selected local
entry invalidate the prepared workflow. Conflicts prevent publication. A failed
publication requires another live check before retrying. The helper supports new
text-only entries and content/synonym updates to existing entries that pass the
publisher's checks. Option 1 runs the same checks as option 2 and marks any other
change `[unsupported]` with a `Why:` line; see
[Entries the helper cannot publish](#entries-the-helper-cannot-publish). Do not
run multiple helpers simultaneously.

After publication, verify the site, stop the local server, and choose **8** to
bring website changes home. It checks for unpublished/conflicting edits before
selecting a new baseline and working copy; existing copies are preserved. Read
the comparison report if it refuses to switch, then restart with **6** after a
successful refresh. Option **7** (Set baseline and working paths) is for deliberate
manual configuration of an already verified pair, not routine synchronization;
it does not download, merge or reconcile changes.

### Entries the helper cannot publish

Options 1 and 2 apply the same eligibility rules, so an entry shown as
`[unsupported]` in option 1 will be refused by option 2 with the same reason.
Option 1 only reports; it changes nothing. The publication safeguards in options
3 to 5 are unchanged and still repeat every check.

| Option 1 reason begins with | Meaning |
|---|---|
| `deleted locally` | Deletions are not supported. |
| `changes <fields>` | Only content (`cleaned_tex`) and synonyms of an existing entry can be published. Title, classification, type, definition, link-exclusion and related-concept changes have no helper route. |
| `local version ...` | Your edit itself would fail: empty content, a duplicate or untrimmed synonym, or an image or embed that was added, removed or changed. |
| `has N diagram(s) with no stored SVG` | The entry's PSTricks diagrams have no generated SVG in your working database, so the page would show "[Diagram unavailable]". Choose **19** to render them; option 2 then publishes them with the text (see [Publish a diagram change](#publish-a-diagram-change)). |
| `has diagrams with no rendered SVG` | A changed or new diagram has no SVG in your working copy yet. Choose **19**, then **1** again. |
| `new entry ...` | A new entry fails the new-entry checks (slug, classification, type, media). |

**Existing entries** are checked only on what the edit changes
(`apply_math_text_patch.patch_intended`, shared by options 1 to 5):

- Only content (`cleaned_tex`) and synonyms may change, and content must not be
  empty.
- **Every diagram, image and embed must stay byte-identical and in the same
  order.** This covers PSTricks blocks (`pspicture`, `\pstree`, `\psset`),
  `\includegraphics`, `\input`, `\include`, `figure` and `tikzpicture`
  environments (including their captions), `<img>`, `<svg>`, `<script>`,
  `<iframe>` and `/api/math/diagrams/` references. The prose around them can
  change freely. A changed PSTricks diagram takes the diagram route instead
  (see [Publish a diagram change](#publish-a-diagram-change)), where the same rule
  holds for everything except the PSTricks blocks.
- Each PSTricks diagram must already have a stored SVG. Option 1/2 check the
  working database and the live publisher checks the live database again before
  taking its backup. The text update reuses stored SVGs and never runs LaTeX.
- **Changed** synonyms must be non-blank, trimmed and unique ignoring
  capitalization. Unchanged synonyms are left exactly as stored.
- Metadata the edit does not touch is not judged: a missing classification or
  type, a duplicate defined term or an older-style slug no longer blocks a text
  fix. Fix those separately (production-first, below) when you want to.

**New entries** still go through `publish_math_entry.validate`, which rejects:

- **Diagrams or media in the body** (any of the items listed above). PSTricks
  diagrams are allowed through the diagram route; other media are not.
- **No MSC classification or no document type.**
- **Synonyms, defined terms, link exclusions or related concepts with a
  duplicate or a value with leading/trailing spaces.** Synonyms that differ only
  in capitalization are also rejected.
- **A slug that is not lowercase words joined by hyphens.** The editor refuses
  such slugs for entries created since 2026-10-22.

On 2026-10-21, 75 existing entries failed the old existing-entry checks. Text
and synonym fixes now work for the 16 entries without a classification or type
or with duplicate metadata, and for diagram entries whose diagrams are untouched
and have stored SVGs. Entries such as `deduction`,
`derivations-in-natural-deduction` and `rooted-tree` contain `\pstree` with no
stored SVG; option 19 renders them and option 2 publishes them through the
diagram route. Option 1 is the source of truth for any entry you
have edited.

**Production-first is not a universal workaround.** Editing on the live site
(after a fresh backup, as in
[Adding a math entry](../../features/math/ADDING_ENTRIES.md#b-production-first-create-live-then-synchronize-locally))
and then bringing the change home with option 8 is reasonable only for:

- metadata fixes with unchanged text (adding a missing classification or type,
  removing a duplicate term); the editor re-renders using the stored diagrams;
- text edits that leave every PSTricks block (`pspicture`, `\pstree`)
  byte-identical; check the live page for "[Diagram unavailable]";
- text edits near `\includegraphics`/`figure` that leave the image references
  unchanged; check that the images still show.

It is **not** a route for any change inside a PSTricks block, a new diagram, or new
or changed image files. The live editor would render diagrams on the server, and
server-side LaTeX/dvisvgm support is unverified; nothing transfers image files.
Publish PSTricks changes through the diagram route instead; new or changed image
files still have no supported route, so keep those local. The
production-first behavior above comes from reading the editor and update routes,
not from a live test.

### Check whether the server can render diagrams

This read-only check answers whether PythonAnywhere can render PSTricks at all:

```powershell
.\.venv313\Scripts\python.exe backend/probe_server_diagrams.py --output dist\diagram-probe.txt
```

It uses the same SSH route as option 4, so SSH may ask for the account
password. On the server it reports whether `latex`, `dvisvgm` and the PSTricks
packages are installed. It renders two fixed samples (a `pspicture` and a
`\pstree`) with the site's own document wrapper, plus one stored live diagram,
in a new folder under the server's temporary directory. Then it deletes that
folder. It compares the stored diagram's SVG with its fresh rendering. The
database is opened read-only, the diagrams folder is only read, and the site is
not reloaded. The report's first line is `SERVER CAN RENDER PSTRICKS` or
`SERVER CANNOT RENDER PSTRICKS`.

A passing check does not make the live editor a safe route for diagram changes.
The editor renders inside its database transaction and writes straight to the
final SVG name. Diagram publication through the helper is planned separately,
with SVGs rendered on the laptop.

### Publish a diagram change

PSTricks diagrams (`pspicture`, with any `\psset` just before it, and top-level
`\pstree`) are rendered **on this computer**, never on the server. Their SVGs
travel in the package with the entry. This covers:
- an existing entry whose diagrams changed, with or without content or synonym
  edits;
- a new entry with diagrams;
- an entry whose diagrams have no stored SVG, such as `deduction`,
  `derivations-in-natural-deduction` and `rooted-tree`.

`\includegraphics`, `figure`, `tikzpicture`, `<img>` and other media must still
stay exactly as they are.

1. Edit and save the entry in the local editor. The editor renders a diagram
   only when its source changed. For diagrams that are still missing (option 1
   says to choose 19), choose **19** and give the canonical name. Option 19
   renders each missing diagram with LaTeX and dvisvgm in a throwaway folder,
   checks the SVG, then links it into `backend/data/math/diagrams/` without
   replacing any file. It then stores the diagram rows and page in the working
   copy. Valid existing SVGs are reused. An unusable same-named file stops it
   and is left for you to remove. Check the page on the local server.
2. Option **1** lists the entry with `diagrams` among its changes. Option **2**
   builds the package: `diagrams.json` plus one `svg/<hash>.svg` per diagram.
   Every SVG must be well-formed and contain no scripts, event handlers or
   outside links. The review lists diagrams added, kept and removed.
3. Options **3**, **4** and **5** stage, check and publish as usual. The live
   check reads each target SVG on the server. It also confirms that the live
   entry and its diagram rows still match what you prepared.

On the server, the publisher places the files before it changes any row:
1. It writes a journal, `~/backups/diagram-publish/<package SHA-256>.json`.
2. It writes each SVG into `backend/data/math/diagrams-incoming/` (never served),
   checks its SHA-256, then links it into the diagrams folder. A link never
   replaces a file.
3. Only after every file checks out does it take the usual verified database
   backup. Then, in one transaction, it updates the entry and replaces that
   entry's diagram rows. The page is rebuilt from the stored SVGs, without LaTeX.

A file already on the server under the same name with **different** bytes is a
rendering of the same diagram source (names come from the source). If it is a
valid SVG it is kept and reported. If it is not, the check stops and nothing is
written. Old SVGs from replaced diagrams stay on disk, because another entry may
use the same source.

**If a publish is interrupted,** the database is unchanged unless the commit
finished. Any file already placed is complete and simply unused. Run option
**4** again: it reports either `EXPECTED TEXT MATCHES` (publish the same package
again with **5**; placed files are skipped) or `ALREADY PRESENT` (the commit
finished).

To clean up after a publish you abandon, or after restoring the database from
the journal's backup, list the journals and then the leftovers of one publish.
Neither command changes anything without `--apply`:

```powershell
.\.venv313\Scripts\python.exe backend/diagram_recovery.py
.\.venv313\Scripts\python.exe backend/diagram_recovery.py --package <package SHA-256>
.\.venv313\Scripts\python.exe backend/diagram_recovery.py --package <package SHA-256> --apply
```

It removes only SVGs that this publish created, that no diagram row references
and that still hold the published bytes, plus unfinished incoming folders. To
undo a committed publish, restore the journal's `backup` the way
[Backup and recovery](../backups/BACKUP_RECOVERY.md) describes, then run the
cleanup.

The same commands work from the command line: `backend/diagram_sync.py
render-missing --db <working.db> --canonical <name>` and `backend/diagram_sync.py
prepare --base <base.db> --local <working.db> --canonical <name> --output <zip>`.

Until option 8 learns to compare diagram rows by content (next change), it stops
after a diagram publish with "File-backed content changed". Your working copy is
not affected.

## Upload a reviewed package through the API

After configuring `backend/pythonanywhere_api.py setup` and passing its `check`,
run this in the VS Code terminal with a ZIP whose contents you have reviewed:

```powershell
.\.venv313\Scripts\python.exe backend/stage_pythonanywhere_package.py dist/metric-space-review.zip
```

This example stages the previously reviewed metric-space package for a transfer
test. That entry is already live: do not apply it again.

The generic uploader accepts other reviewed update ZIPs. It uploads into a new
`/home/cwoo/chi-portfolio-staging/<unique-id>/package.zip`, downloads it again,
and compares SHA-256 hashes. It never extracts or executes the package, changes
the live database, or reloads the website. Keep the printed path for the separate
publication step. No account password is prompted; the private API token is used.

ZIPs are limited to 50 MB compressed and expanded. Unsafe archive paths,
databases and known private configuration filenames are rejected. This is not a
secret scanner: review the contents before uploading. A failed transfer may leave
an unverified staging file; a retry uses a fresh folder. Old staging folders can
be removed through PythonAnywhere Files after they are no longer needed.

Uses the official file upload API: https://help.pythonanywhere.com/pages/API/

### Inspect the staged package

Use the exact remote path printed by the uploader:

```powershell
.\.venv313\Scripts\python.exe backend/inspect_staged_package.py REMOTE-STAGING-PATH --local dist/metric-space-review.zip --output dist/staged-review.txt
```

The inspector uses only a GET request, verifies the ZIP against the original
local package, and writes a new local report. It does not extract or execute
bundled scripts. It supports one new-entry or existing-text-patch JSON payload;
other package types are rejected. Read the report for the file inventory and
proposed entry content or text diff. Inspection does not audit bundled code.

Optionally add `--snapshot PATH-TO-FRESH-LIVE-SNAPSHOT` to check duplicates,
required metadata, already-present entries, or expected-text conflicts against
that snapshot. Without it, live eligibility is explicitly not checked. Even
with it, publication must repeat checks against the live database in a write
transaction. The inspector never authorizes or applies publication itself.

## Check a staged package against the live database

In a regular VS Code terminal (not PowerShell ISE):

```powershell
.\.venv313\Scripts\python.exe backend/preflight_live_package.py REMOTE-STAGING-PATH --local dist/metric-space-review.zip --output dist/live-preflight.txt
```

Replace the staging path with the one printed by the uploader. SSH may prompt
once for your PythonAnywhere account password. The tool sends the local reviewed
checker modules through SSH to run in memory; it does not install scripts or run
code from the ZIP. It verifies the staged ZIP against the local SHA-256 and opens
the actual live database read-only in a consistent transaction.

Read the report for `ALREADY PRESENT`, an eligible-for-further-review result, or
`BLOCKED`/`CONFLICT`. Unsupported or malformed packages fail the check. A report
is not publication approval: live content can change afterward, so a publisher
must recheck under a write lock. No extraction, backup, database update or web
reload is performed by this command. Each report requires a new output filename.

## Publish one new text-only entry

### Prepare an existing entry's content and synonym changes

```powershell
.\.venv313\Scripts\python.exe backend/prepare_math_patch.py --base dist/sync-first-test/base.db --local dist/sync-first-test/working.db --canonical CANONICAL-NAME --output dist/entry-update-review.zip
```

Use the actual unchanged baseline from which the working copy was created.
The reusable preparer requires both copies to contain the entry and rejects
changes outside content and synonyms. It packages the full expected baseline
record plus the proposed content and optional replacement synonym list. Review
the text diff and synonym additions/removals before staging. Existing text-only
packages remain supported and preserve synonyms.

Preflight checks the full expected entry, including its synonyms. Publication
repeats that check under the write lock, creates a verified backup, then updates
content and synonyms in the same transaction. A failure rolls back both changes.
Synonym changes on the live entry cause a conflict, even if its text still
matches. An already-applied package is skipped only when both content and
synonyms match. These checks do not establish mathematical correctness or detect
aliases belonging to other entries; review meaning and cross-entry naming before
publication.

### Publish a staged package after reviewing live preflight

```powershell
.\.venv313\Scripts\python.exe backend/publish_staged_package.py REMOTE-STAGING-PATH --local dist/REVIEWED-PACKAGE.zip --output dist/publication-receipt.json --apply
```

Use the same reviewed ZIP and staging path used for preflight. The explicit
`--apply` command publishes one supported new entry or existing-entry text patch.
It uses the host's `chi-portfolio` virtualenv and sends trusted local publisher
modules through SSH; code bundled in the ZIP is never executed. The staged ZIP
must still match the local digest. Identical existing content returns
`ALREADY_PRESENT` without a backup or update. Otherwise the transactional updater
rechecks duplicates/expected content under a write lock, creates a verified
backup, applies only the selected entry, verifies it, and commits.

The receipt records `APPLIED` and the backup path, or `ALREADY_PRESENT`. An SSH
failure or interrupted command can leave a `PENDING` receipt even if the server
committed. Keep it and run live preflight before retrying. Never assume a failed
connection means an update was rolled back. Use a new receipt filename per run.
After a successful change, verify the page and download a new baseline. No web
reload is performed. This command does not publish site files, media, deletions,
or biography/resume changes.

### Prepare a new entry package

Create the new concept in a working copy of a known live baseline. Download a
fresh live snapshot and run the three-way comparison. Review the mathematics,
metadata, search/autolinks and rendering locally before packaging it.

```powershell
.\.venv313\Scripts\python.exe backend/publish_math_entry.py prepare --base dist/sync-first-test/base.db --local dist/sync-first-test/working.db --live PATH-TO-FRESH-LIVE-SNAPSHOT --canonical NEW-CANONICAL-NAME --output dist/new-entry-review
```

Replace the uppercase placeholders with actual values. Inspect `entry.json` and
`REVIEW.txt`. The tool rejects entries already in the baseline, duplicate live
titles/slugs/canonical names, and titles already listed as defined terms or
synonyms. It does not prove semantic uniqueness: manually search the collection
for equivalent definitions first. Other alias collisions require editorial review.

Upload the three files `entry.json`, `publish_math_entry.py` and
`preview_math_sync.py` into a new private folder such as `/home/cwoo/new-entry-review`
on PythonAnywhere (never inside frontend). In its Bash console:

```bash
workon chi-portfolio
python /home/cwoo/new-entry-review/publish_math_entry.py apply /home/cwoo/new-entry-review/entry.json
```

The live operation repeats duplicate and metadata checks under a database write
lock, creates a consistent verified backup in `/home/cwoo/backups`, inserts one
entry with fresh IDs, resolves metadata by name/code, regenerates rendering and
verifies the stored content before committing. It never replaces an existing
entry. A second application is rejected. Inspect the new entry, classification
listing, search and autolinks on the live site, then download the new baseline.

Only text/equation entries are supported in this increment. No assets, diagram
generation, missing classifications/types, or missing related concepts are
imported. Publish dependencies separately first. Backup restoration remains a
separate reviewed recovery operation; do not restore over a running database.

## Downloading the live snapshot

In a normal VS Code terminal or Windows Terminal (not PowerShell ISE):

```powershell
cd C:\Development\chi-portfolio
.\.venv313\Scripts\python.exe backend/download_live_database.py
```

The downloader creates `Downloads/chi-portfolio/database/<UTC timestamp>/` under
your Windows home folder, containing `live-snapshot.db` and `snapshot.json`.
Use `--destination PATH` if Windows Downloads is redirected elsewhere. Each run
creates a fresh snapshot; it does not reuse an older download or replace the
working database. Preserve the first snapshot unchanged as your comparison base.

It uses SSH and SCP with normal host verification and interactive authentication.
Use your **PythonAnywhere account password**, not the portfolio admin password.
No password is stored by the script. You may be prompted twice. On a first
connection, compare the host fingerprint with PythonAnywhere's official guide
before accepting: https://help.pythonanywhere.com/pages/SSHAccess/

On the server it uses SQLite's backup API (not a raw copy of an active database),
retains the snapshot in `/home/cwoo/backups/`, and checks its integrity. Locally,
the downloader verifies its SHA-256 and database integrity before marking it
complete. Failed downloads remain `.partial` and must not be used. Server
snapshots consume hosting quota; periodically remove older ones through Files
after confirming your retained backups. The script never deletes them itself.

This downloads database content only, not media files. Keep snapshots private.
The downloaded database is a base for the NEXT local editing session; it cannot
retroactively establish a common base for changes already made on your laptop.

## Comparing snapshots

This tool writes a JSON report, never database changes. It runs locally and
does not connect to PythonAnywhere. Keep snapshots and reports private, outside
Git (for example in ignored `dist/sync/`).

Before starting future local content work, download a consistent live backup.
Keep it unchanged as `base.db`; work on a separate copy. When ready to compare,
download another live backup as `live.db`. The base must be the actual snapshot
from which local edits began. An arbitrary old local database is not a substitute.
For earlier edits with no known common snapshot, review differences manually.

```powershell
.\.venv313\Scripts\python.exe backend/preview_math_sync.py --base dist/sync/base.db --local backend/portfolio.db --live dist/sync/live.db --output dist/sync/preview.json
```

Use a new report filename each time. Missing or incompatible databases fail
closed. Every input is opened read-only, in a read transaction, and checked for
integrity and broken foreign keys.

Report outcomes:

- `local_only_review`: local changes proposed for human review, not applied.
- `live_only_preserve`: live edits must be preserved; local remained unchanged.
- `conflict`: both sides changed the same entry differently. Review all fields.
- `already_equal`: both sides now agree; nothing to transfer.

New entries and deletions have explicit presence flags. Deletions always require
manual review. A deliberate reversal made after the base snapshot appears as a
local change; an unchanged old local value does not override a newer live edit.

Matching uses canonical names, not database IDs. Renames appear as removal plus
addition and require manual review. Compare title, slug, owner, source TeX,
cleaned status, classification codes, types, synonyms, defined terms, link
exclusions and related canonical names. Do not infer that a report with no
changes means the entire databases match: timestamps, generated rendering,
diagrams/media, import records, and non-math content are outside this first step.
Assets and regenerated rendering must be checked before any future publication.

The preview command never applies changes. Separate targeted publishers exist
for text changes and new text-only entries. They recheck live records inside a
write transaction; a snapshot report alone does not authorize overwriting a
database that has changed since the snapshot was taken.

The helper is now named `website_workflow.py`. The old `math_workflow.py` command
still works. Existing saved settings and package folders keep their original
names so no paths or workflow state need to be migrated.
