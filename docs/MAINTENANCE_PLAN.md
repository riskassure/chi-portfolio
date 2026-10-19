# Maintenance assessment plan

Status: documentation baseline committed. A first-pass static inventory and
dependency review is recorded in [the maintenance assessment](MAINTENANCE_ASSESSMENT.md).
The documentation index and current-workflow pointers have been added. Code
maintenance work is proceeding in focused batches.
The [tracked backup review](BACKUP_REVIEW.md) and authorized private preservation
are complete. This change untracks the verified backup while retaining its local
copy and adds an ignore rule. Earlier Git history remains unchanged.
The music catalog's historical publication algorithm has now been extracted into
`history_publication.py`, preserving `music_catalog.publish` as a lazy compatibility
entry point. The current refresh and query path is tested with historical modules
unavailable. This refactor changes no schema or schedule and was deployed October 18, 2026.

Map and gallery persistence now share `services/file_persistence.py` for exclusive
lock ownership and flushed atomic file replacement. Feature validation,
serialization, revision-check timing and conflict exceptions remain with their
original services. Seventeen targeted persistence/map/gallery tests pass. This
change was deployed October 18, 2026, with the new helper, `travel_store.py`
and `gallery_settings.py` together. Public music, photography and map APIs and
browser pages passed verification; no live editor writes were performed.

## Sequence

The [configuration review](CONFIG_REVIEW.md) identified implicit setup dependencies
in the older playlist parser and photo converter. Removing config's import-time
directory creation requires addressing those utilities and testing a fresh
workspace first. This is now implemented locally with isolated setup/import tests;
all 205 regression tests passed. Deployed October 18, 2026 with successful
reload and read-only public verification; details are in the admin runbook.

1. Verify and review the admin runbook against actual workflows.
2. Inventory production entry points, local tools, reusable services, tests,
   configuration, generated data, historical scripts, and backups. Identify
   callers and operational dependencies before calling anything unused.
3. Record findings with file references, concrete problem, proposed change,
   expected benefit, risk, verification, and rollback approach.
4. Prioritize small changes that reduce maintenance burden. Separate structural
   cleanup from measured performance problems; measure before optimizing.
5. Implement one agreed area at a time, preserving behavior and user data.
6. Test the affected behavior, update documentation, and commit focused changes.
   Deploy only applicable production changes and verify them separately.
7. Agree on retention and archive/delete candidates separately from code cleanup.

## Candidates to investigate (not established defects)

The owner confirms that mathematics already underwent extensive modularization
and simplification. Keep further math restructuring low priority, review its
history first, and require a concrete maintenance problem or measured bottleneck.
Large files alone do not establish a need for another refactor.

- Older Spotify export/history tools versus the current top-track workflow.
- Repeated preparation, staging, validation and publication code.
- Large route modules mixing HTTP handling and database operations.
- Multiple database snapshots, review scripts and generated artifacts.
- Conflicting or outdated instructions across existing Markdown guides.

## Assessment deliverable

A table of proposed changes, ordered by value and risk, with evidence and a
recommended first batch. Include an explicit keep/archive/remove classification
only after checking usage. Do not infer that a file is disposable from age, size,
name, or its presence in `dist`.

## Pending operational checks

- Completed October 18: verified the October 17 automatic Spotify run via its
  hosting task log (exit code 0, 50 tracks) and matching public ranking timestamp.
- Completed October 18: bounded local/production inventory and isolated recovery
  of a historical database snapshot. Five application queries passed. See
  [backup and recovery review](BACKUP_RECOVERY.md). A subsequent full-site archive was created on hosting, downloaded privately,
  checksum-verified and restored in isolation: ten page/API checks, 18 photos and
  76 diagram references passed. Hosting/credential restoration and an additional
  off-device copy remain unverified; retention policy is proposed, not enacted.
