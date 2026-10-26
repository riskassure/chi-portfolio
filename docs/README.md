# Website documentation

Start with the [admin runbook](ADMIN_RUNBOOK.md) for everyday editing,
publication, database copies, backups, credentials and Spotify refresh.
Committing code does not publish it to the website.

## Operating the website

| Guide | Use it for |
| --- | --- |
| [Admin runbook](ADMIN_RUNBOOK.md) | Current operating procedures and recorded deployment status |
| [How the website works](administration/HOW_THE_SITE_WORKS.md) | Browser vs server, reloads, caching, logins, developer tools and where errors appear |
| [Content synchronization](administration/deployment/CONTENT_SYNC.md) | Detailed helper preparation, checks and publication |
| [Travel map](features/travel/TRAVEL_MAP.md) | Map editing, reference data, photo bindings and gallery settings |
| [Spotify](features/music/SPOTIFY.md) | Current top-track workflow; older export workflow is labeled separately |
| [Google Photos](features/photography/GOOGLE_PHOTOS.md) | Photo import implementation and setup |
| [Math authoring](features/math/AUTHORING_STANDARDS.md) | Mathematics content conventions |
| [Adding a math entry](features/math/ADDING_ENTRIES.md) | Local create/preview/save steps and reviewed publication |
| [Math frontend](features/math/FRONTEND.md) | Mathematics frontend implementation notes |
| [Merge candidates](features/math/MERGE_CANDIDATES.md) | Read-only report of entries to merge, cross-link or rename |
| [Merging and retiring entries](features/math/MERGING_ENTRIES.md) | Option 21: merge an entry into another, retire one, undo; rollout and rules |
| [Batch publishing design](features/math/BATCH_PUBLISHING_DESIGN.md) | Agreed design behind option 20 (implemented); why it works as it does |
| [Merging design](features/math/MERGING_DESIGN.md) | Approved design v3 behind option 21 (implemented); why it works as it does |

## Backup administration

- [Tracked backup review](administration/backups/HISTORICAL_BACKUP_REVIEW.md): provenance, integrity checks and preservation history.
- [Backup and recovery review](administration/backups/BACKUP_RECOVERY.md): inventory, isolated restore results and proposed retention; not a complete disaster-recovery procedure.

## Maintenance

- [Maintenance plan](maintenance/MAINTENANCE_PLAN.md): scope, sequence and pending checks.
- [Assessment](maintenance/assessments/REPOSITORY_ASSESSMENT.md): findings and proposed priorities, not a deletion list.
- [Configuration review](maintenance/assessments/CONFIG_REVIEW.md): directory-creation dependencies and proposed explicit setup.
- [Agent instructions](../AGENTS.md): expectations for future coding sessions.

The math section has already undergone substantial modularization and
simplification, as confirmed by the owner. Review that history before proposing
further changes. File size alone is not a reason to refactor it again.

## Math sources and historical audits

- [Knot diagram sources](features/math/KNOT_SOURCES.md): retained image provenance and source files.
- [Algebra definition audit](maintenance/history/ALGEBRA_DEFINITION_AUDIT.md): historical subject-specific findings.
- [Category definition audit](maintenance/history/CATEGORY_DEFINITION_AUDIT.md): historical subject-specific findings.
- [Migration scripts review](maintenance/history/MIGRATION_SCRIPTS_REVIEW.md): what each historical math migration script changes.

## Historical and alternative deployment references

| Guide | Context |
| --- | --- |
| [PythonAnywhere first installation](administration/deployment/PYTHONANYWHERE.md) | Initial hosting setup; do not repeat over the live site |
| [Manual update and recovery](administration/deployment/MANUAL_UPDATES.md) | Older package-based updates and recovery detail; use the runbook for routine updates |
| [Generic deployment preparation](administration/deployment/GENERIC_HOSTING.md) | Alternative Waitress hosting design, not the current PythonAnywhere setup |

## Folder organization

- `administration/`: [How the website works](administration/HOW_THE_SITE_WORKS.md).
- `administration/deployment/`: publishing, synchronization and hosting references.
- `administration/backups/`: backup inventories and recovery results.
- `features/`: math, music, photography and travel guides.
- `maintenance/assessments/`: scoped technical reviews.
- `maintenance/history/`: historical subject-specific audits.

`AGENTS.md` remains at the repository root. Short component README files link here
and to their feature guides. The deployment package builder includes this docs
folder and AGENTS.md; older archives retain their original documentation layout.
The October 21 reorganization changes documentation locations, not website routes.

Keep procedures synchronized with implementation. Label historical facts and
unverified operational checks explicitly, and never include credential values.
