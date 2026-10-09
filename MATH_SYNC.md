# Incremental math synchronization

## Guided helper (recommended)

### Bring website changes home (menu option 8)

Stop the local server, then select **8** and type `STOPPED`. The helper downloads
a new verified live snapshot using the existing SSH downloader (which may ask
for the PythonAnywhere account password twice). It compares every database table
against the remembered baseline and working copy, not just math fields.

It allows a refresh only if each local table is unchanged from the baseline or
already exactly matches live. This first version is deliberately conservative:
different IDs, timestamps or audit rows can require manual review even when the
visible content looks identical. It stops on divergent local rows, schema changes,
or differences in media-related tables. It does not merge unpublished edits.

On success it creates verified `base.db` and `working.db` in a new ignored
`dist/home-sync/<unique-id>/` folder and remembers those paths. The original
databases, downloaded snapshot, and previous workflow settings are preserved.
Choose **6** to restart the local server on the refreshed working copy. The
baseline must remain unchanged. A comparison report is saved on both successful
and blocked comparisons. No live database writes or reloads are performed.

This is database synchronization only. Website program files and media files
are not downloaded or reconciled. Stop the local server before switching copies
so it does not keep writing to the old database. Do not run concurrent helpers.

```powershell
.\.venv313\Scripts\python.exe backend/math_workflow.py
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
text-only entries and existing content/synonym updates; other metadata edits and
deletions are listed as unsupported. Do not run multiple helpers simultaneously.

After publication, verify the site and download a fresh baseline using the
existing downloader. Preserve unpublished edits before refreshing the working
copy, then choose Set baseline and working paths. No databases are automatically
replaced. Start local server uses the remembered working copy and asks for the
usual session password; stop any existing local server first.

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
