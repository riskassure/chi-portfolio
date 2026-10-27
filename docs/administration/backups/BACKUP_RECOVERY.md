# Backup and recovery review

> Update 2026-10-27: nightly live database backups with automatic retention now
> exist; see [NIGHTLY_BACKUPS.md](NIGHTLY_BACKUPS.md). The statements below that no
> schedule or retention policy is installed describe October 18.

Reviewed October 18, 2026. Production backup inventory and recovery-source access
were read-only. No existing backup, live database, schedule or website file was
modified. Private test details are in ignored `dist/backup-*-inventory.json` and
`dist/backup-recovery-result.json`.

## Inventory scope and findings

| Inspected location | Files/items | Approximate size | Interpretation |
| --- | ---: | ---: | --- |
| Local `backend` (*.db, *.zip) | 70 | 1,478.1 MiB | Includes active database, historical review copies and backups; not all disposable backups |
| Local `dist/home-sync` | 12 | 192.0 MiB | Baselines and working database copies |
| Local `dist/math-workflow` | 12 | 2.1 MiB | Packages/database files; receipts and reports are additional |
| Downloads/chi-portfolio/database | 11 | 175.9 MiB | Downloaded live snapshots |
| Private local backups folder | 1 | 17.2 MiB | Preserved July historical snapshot |
| Production `/home/cwoo/backups` | 28 | 320.0 MiB | 20 database snapshots, seven code-backup directories and one frontend-backup directory |

This is a bounded inventory, not a search of the entire computer or hosting
account. No full-site ZIP was found in the inspected production backup folder.
Other storage locations or external backups may exist. Counts are point-in-time;
no duplicate-file deletion was inferred from names or sizes.

## Recovery exercise completed

Source: `/home/cwoo/backups/before-spotify-top-20261017T155529Z.db`.
This is a historical snapshot before the new top-track publication, not the most
recent live database. It is not recommended as today's production restore point.

Procedure:

1. Read the source SHA-256 through SSH without opening the live database.
2. Download the existing backup into a unique OS temporary directory.
3. Compare SHA-256, then open the copy in SQLite read-only mode for integrity and
   foreign-key checks.
4. Start a separate Python process with `PORTFOLIO_DB_PATH` pointing to that copy.
   Use Flask's in-process test client with current local code; no HTTP server,
   scheduled refresh or content-edit request was started.
5. Exercise the music, current gallery, travel-photo, math-classification and math
   search endpoints. Compare the copy's checksum again afterward.
6. Remove only the temporary copy and empty exercise folder, keeping originals.

Results:

- SHA-256: `09b9e0d23fd5efa0be369128400ca0651a7dd51f00989c35848ad2dd6841603d`.
- SQLite integrity: `ok`; zero foreign-key violations.
- Source catalog counts: 2,461 music rows, 18 photographs, 1,182 math concepts.
- All five application endpoints returned HTTP 200.
- Restored copy's checksum unchanged after the queries.
- Windows initially delayed cleanup because the review script retained a database
  handle. After the process exited, the temporary file was hash-checked and removed;
  the script now explicitly closes the connection. Existing backups were untouched.

This proves database readability and selected query compatibility with current
local code. It does not prove full-site recovery, all records' correctness,
media availability, private credential recovery, admin writes, Linux restoration,
or reinstatement of hosting/schedules. A restored database alone cannot recover
photo files or the file-based travel edits.

## Existing backup tools

`backend/backup_database.py` creates a new SQLite snapshot and checks integrity.
`backend/backup_site.py` packages frontend/backend files and a consistent SQLite
snapshot into a new archive outside the site directory; it verifies ZIP CRCs.
The full-site tool was inspected, not executed during this review.

The full-site tool excludes hidden paths, most backend raw data, virtualenvs and
private home-directory settings. It includes generated math diagrams. Its database
source is explicitly `backend/portfolio.db` under the supplied root, not the helper's
selected working copy. It is intended for a known site root; inspect the resulting
manifest/file list before relying on it as a full recovery source.

An ordinary code publication backup covers changed files, not the whole site.
Database snapshots do not cover media, map data files or credentials. Git covers
tracked code and assets, but not current live database contents or private settings.

## Proposed retention policy (not enacted)

- Preserve the helper's selected baseline and working copy, active package/receipt,
  and every copy with unpublished edits until reconciliation is complete.
- Retain each pre-release backup until the release has been verified and a newer
  recovery set is established. Keep at least the last three verified releases.
- For future scheduled database snapshots: retain seven daily, four weekly and
  six monthly recovery points, subject to measured hosting quota.
- Preserve milestone/historical snapshots with provenance until explicitly reviewed;
  age alone is not permission to delete them.
- Keep a verified current full-site recovery archive off the hosting account, and
  another protected copy off this computer. Choose the destination before transfer.
- Back up credentials separately with encryption/access controls. Document hosting
  configuration and scheduled-task commands without embedding secret values.
- Repeat an isolated restore exercise after significant schema/hosting changes,
  and periodically for the latest full recovery set.

No backup schedule or automatic deletion policy has been installed. These are
proposals, not evidence that daily/off-device backups already exist. The full-site
backup tool does not encrypt archives. Storage consumption should be checked before
adopting retention counts, especially for full-site media archives.

## Recommended next step

Create a current full-site archive on PythonAnywhere, download and checksum it into
private storage, then extract/test it in an isolated directory. Keep private settings
separate and record how they would be restored. Confirm an off-device destination
and retention policy before copying secrets or deleting any older backups.

For a real incident, preserve the current state first, stop relevant writes/jobs,
and plan restoration of the appropriate database/files. Do not replace an open
SQLite database or restore a whole old site over current content. Consult the
admin runbook and obtain a specific recovery plan for the incident.

## Full-site archive and isolated restore completed October 18, 2026

Created a new archive with the reviewed `backup_site.py` implementation, using
an owner-only creation mask on PythonAnywhere. Existing backup files and live
website content were not changed. Archive creation reads site files sequentially;
it is not an atomic snapshot of concurrent file edits. The SQLite snapshot is
consistent. Avoid editing/deploying while creating future recovery archives.

- Server: `/home/cwoo/backups/full-site-20261018-6775c038.zip`.
- Local: `%USERPROFILE%\.config\chi-portfolio\backups\full-site\full-site-20261018-6775c038.zip`.
- Size: 20,186,623 bytes (approximately 19.3 MiB).
- SHA-256: `2ba7c626194f7747597f28d1f64e81d602712f63a80c3dd39e707a57e254afd7`.
- Local companion: `full-site-20261018-6775c038.verification.json`.

The download matched the remote checksum. ZIP CRC checks passed. Archive paths
were checked for traversal and symlinks before extraction into a unique temporary
folder. Every extracted file's hash matched its archived bytes. Configuration,
code, map data and media were loaded from that isolated restored tree, with the
installed local Python environment providing dependencies.

SQLite integrity and foreign-key checks passed. All 18 catalog photographs were
present and served successfully; all 76 referenced diagram filenames existed in
the restored diagram directory. Ten public page/API requests passed, including
home, music, photos, map, math search/classifications, and travel data. The restored
database hash remained unchanged. The temporary extraction was removed afterward;
both archives and the verification record remain.

Private hosting/API/Spotify credentials and the Esri key were excluded. This was
not a test of DNS, TLS, PythonAnywhere WSGI installation, fresh dependency install,
admin writes, external Spotify/Esri connections, browser rendering, or scheduled
job reinstatement. No credentials were copied into the test tree. Re-create the
hosting environment from the runbook and supply protected private settings
separately during a real recovery. The archive is not encrypted.

The previously identified code/media/database recovery gap now has a tested
archive. An additional protected copy off this computer and hosting account,
credential recovery, and a formal retention/automatic backup policy remain
separate decisions. No deletion policy or backup schedule was installed.
