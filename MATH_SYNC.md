# Incremental math synchronization

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

## Increment: publish one new text-only entry

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
