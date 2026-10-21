# Tracked database backup review

Reviewed: 2026-10-17. Scope: read-only history, reference and SQLite checks.

## File and provenance

`backend/backups/portfolio_before_local_macro_backfill_20260728_205948_390296.db`
was introduced in commit `678d7de` (`Add safeguarded local macro backfill
migration`, July 28, 2026), alongside
`backend/src/database/math/migrations/backfill_local_macro_preludes.py`.
That migration generates timestamped backups using SQLite's backup API before
applying changes. The filename matches that procedure.

No exact-filename references were found in the searched repository source and
documentation, apart from the maintenance assessment. The migration generates
new filenames rather than depending on this particular snapshot. This is not
proof about external scripts or manual recovery usage.

## Verification

- Size: 18,006,016 bytes (approximately 17.2 MiB).
- SHA-256: `c07f8271049dbe7e98990ae3b6c777cf87bd6d602f222f6e5157c97cc017260b`.
- Opened with SQLite `mode=ro` and `PRAGMA query_only=ON`.
- `PRAGMA integrity_check`: `ok`.
- `PRAGMA foreign_key_check`: zero reported violations.
- File hash unchanged after inspection.

Schema names include math content/audit tables, `music_catalog`,
`photography_catalog`, `stg_math_import`, and `stg_spotify_import`. This is a
historical portfolio snapshot, not merely a math-only fixture. Table contents
were not exported or reviewed for sensitive information. No restoration test
was performed; integrity alone does not prove application-level recoverability.

## Preservation completed

The owner authorized preservation and untracking after the read-only review.
The archive was copied to the folder below and verified against the recorded
SHA-256, with SQLite integrity `ok` and zero foreign-key violations. A companion
`.provenance.json` records its source, checksum and originating commit.
The original local file is retained. Git tracking is removed in this change,
and database backups under `backend/backups/` are ignored for future additions.
Earlier Git history is unchanged.

## Preservation procedure

Preserve the snapshot privately for historical recovery, then stop tracking it
in future commits. Do not restore it over the current website or working copy.

Verified archive folder:
`C:\Users\riska\.config\chi-portfolio\backups\historical\`.
Being outside Git does not itself encrypt a backup or provide protection against
disk failure. Both copies are on the same computer.

Procedure used for this preservation step:

1. Copy the snapshot to the agreed private archive without overwriting an existing
   file. Record provenance and the checksum alongside it.
2. Verify the copy's checksum and SQLite integrity before changing Git tracking.
3. Add an ignore rule for database backups under `backend/backups/` and untrack
   this file while leaving its existing local copy intact.
4. Review and commit the tracking change. Do not rewrite Git history as part of
   this operation: the file remains in earlier commits unless a separate history
   cleanup is planned and authorized.

The initial review was read-only; the subsequent authorized preservation step
copied and untracked the backup. No local backup was deleted and nothing was deployed.
No general backup retention policy has been established.
