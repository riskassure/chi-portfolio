# Repository maintenance assessment

Date: 2026-10-17. Baseline commit: `5d3a828`.
Scope: first-pass static inventory and dependency review. No code execution,
production inspection, database-content inspection, performance measurement,
refactoring or deletion was performed for this assessment. This is not a full
security audit or proof that every unused-looking script is safe to remove.

## Inventory

Git reports 470 tracked files: 191 Python, 84 JavaScript, 16 HTML, 10 CSS,
15 Markdown and one database file, plus data, images and other assets.
There are 36 tracked `backend/tests/test_*.py` modules. Counts exclude ignored
working databases, environments, downloaded data and `dist` artifacts.

| Area | Entry points / responsibilities | Classification |
| --- | --- | --- |
| Production website | `backend/pythonanywhere_wsgi.py` loads `backend/src/app.py`; seven registered route blueprints | Keep |
| Local preview | `backend/start_local.py`, encrypted password helper, selected working database | Keep |
| Publishing | `backend/website_workflow.py`, staging, preflight, publication and backup modules | Keep; refactor only with remote bootstrap coverage |
| Compatibility helper | `backend/math_workflow.py` delegates to website helper; tests still import it | Keep compatibility entry point |
| Current music | Spotify top worker, auth/API client, catalog query service, music frontend | Keep |
| Older music workflow | History, playlist sync, downloads and jobs modules | Retain pending dependency separation; not deletion-ready |
| Travel/gallery | File-based editors, reference data, photo catalog/import services | Keep; investigate shared persistence helper |
| Mathematics | Routes, renderer/services, browser editor, diagram pipeline, diagnostics | Keep; targeted modularization candidates |
| Math migrations/reviews | Historical migrations and diagnostic scripts | Retain pending caller and provenance review; do not rerun in bulk |
| Generated/reference assets | Map reference JavaScript, diagrams and source material | Keep runtime assets; document generation rather than split by size |
| Local snapshots and `dist` | Workflow state, reports, backups and temporary tools | No deletion recommendation without retention inventory |

## Prioritized findings

### 1. Make documentation entry points consistent (low risk; first batch)

[UPDATING_WEBSITE.md](../UPDATING_WEBSITE.md) describes an older whole code-package
workflow, while [the current helper](../backend/website_workflow.py) supports
specific reviewed packages. [TRAVEL_MAP.md](../TRAVEL_MAP.md) includes historical
photo counts and a local-preview deployment narrative. The runbook now provides
context, but people can still enter through an older guide and miss it.

Action: add a documentation index and short current-workflow pointers to older
operational guides. Label historical setup sections. Do not move every document
at once: [build_deployment_package.py](../backend/build_deployment_package.py)
explicitly includes root-level `PYTHONANYWHERE.md` and `UPDATING_WEBSITE.md`.
Moving them requires updating that builder as well as links and references.

Verification: check local links, command targets and packaging references without
running deployment commands. Rollback: revert only the documentation changes.

### 2. Review the tracked database backup (high priority; separate decision)

Git still tracks
`backend/backups/portfolio_before_local_macro_backfill_20260728_205948_390296.db`.
[.gitignore](../.gitignore) excludes `backend/*.db`, but this nested backup is
already tracked. Its contents were not inspected, so this report makes no claim
about what personal or sensitive information it contains.

Action: establish its retention purpose and whether it belongs in private backup
storage. If approved, preserve a verified private copy before removing it from
future commits and adding the appropriate ignore rule. Untracking does not erase
prior Git history. Any history rewrite would be a separate, coordinated task.

Verification: check preserved file hash and SQLite integrity on an isolated copy;
confirm the intended file is no longer tracked and future backups are ignored.
Rollback: recover from the verified private copy. Do not delete the only copy.

### 3. Separate current and historical music responsibilities (medium risk)

[spotify_top.py](../backend/src/services/music/spotify_top.py) imports `tables`
from [music_catalog.py](../backend/src/services/music/music_catalog.py), which
imports `rank_history` and `six_months_before` from the old history module.
Thus the current flow still has an import dependency on historical code even
though it does not use the old ranking algorithm. Old jobs also have direct tests.

Action: separate shared schema/query/edit behavior from export-history publication.
Preserve existing import interfaces initially, then reassess whether historical
entry points should be explicitly archived or retained as supported optional tools.
Do not delete `spotify_history.py` just because automatic refresh replaced exports.

Verification: current top-track tests, legacy publication tests, preservation of
editorial overrides, and local music rendering. Rollback: revert the code change;
this separation should require no schema change or data migration.

### 4. Consolidate file-save mechanics narrowly (medium risk)

[travel_store.py](../backend/src/services/travel_store.py) and
[gallery_settings.py](../backend/src/services/gallery_settings.py) both implement
exclusive lock files, revision checks, temporary writes and atomic replacement.
This is a concrete candidate for shared mechanics, while validation and data
formats should stay with their feature modules.

Action: extract only the common persistence behavior after comparing permission,
cleanup and failure semantics. Avoid a broad framework for two small consumers.
Verification: stale revisions, concurrent saves, invalid input, write failure,
lock cleanup, and existing map/gallery tests. Rollback: restore the two original
implementations; saved file formats must remain unchanged.

### 5. Make configuration imports free of directory creation (medium risk)

[config.py](../backend/src/config.py) calls `verify_system_directories()` when
imported. Merely importing paths creates data directories. This makes read-only
tools and tests harder to reason about and couples configuration to setup.

Action: trace all consumers, then move required directory creation into explicit
startup/setup or feature operations. Preserve every directory actually required
by deployment, imports and diagram generation.
Verification: imports against temporary paths, fresh local startup and relevant
pipeline/setup tests. Rollback: restore current initialization behavior.

### 6. Preserve prior mathematics refactoring (low priority; higher change risk)

Owner clarification after this assessment: the math section already underwent
extensive modularization and simplification. Review that refactoring history
before proposing another change. The sizes below are inventory observations,
not evidence that those improvements need reworking. Proceed only for a specific
problem such as duplication, unclear responsibilities, a defect or measured delay.

Measured tracked-source sizes:

| File | Lines | Observed responsibilities |
| --- | ---: | --- |
| `backend/src/services/math/render_helper.py` | 1,995 | Diagram extraction, delimiter parsing, prose/list/table/bibliography/link conversion |
| `frontend/math/math_editor.js` | 1,605 | Event wiring, loading/saving, preview and diagram-related editor behavior |
| `backend/src/routes/admin_math.py` | 972 | Public lookups/search, admin audit queries, preview, creation and updates |

[concept_render_service.py](../backend/src/services/math/concept_render_service.py),
[smart_save_service.py](../backend/src/services/math/smart_save_service.py), the
diagram pipeline and diagnostics import renderer helpers. The editor is loaded
by both `frontend/math/create.html` and `frontend/math/edit.html`. Existing route
code already delegates some operations to services; extend those boundaries.

Action: first capture representative current outputs for math, links, lists and
diagrams. Extract one cohesive family at a time, preserving old imports during
transition. Split route responsibilities only after mapping authentication and
transaction boundaries. Avoid a simultaneous rewrite of Python and browser code.

Verification: fixture-based render comparisons, existing diagram-protection tests,
create/edit/preview/save browser checks and public concept pages. Existing tests
are a starting point, not evidence of complete renderer coverage. Rollback: revert
one extraction at a time without schema changes.

### 7. Preserve publishing safeguards when reducing repetition (medium/high risk)

[website_workflow.py](../backend/website_workflow.py) repeats package/job setup
across content types, but their validation and publication rules differ.
[preflight_live_package.py](../backend/preflight_live_package.py) sends an explicit
ordered module list to the remote interpreter; the publisher extends it.
Extracting a shared dependency without updating that list can break remote checks
although normal local imports succeed.

Action: document the request/package/receipt contracts first. Consider small common
job-construction helpers while keeping content-specific checks explicit. Do not
merge photo removal, metadata updates and code publication into one generic
operation solely because their scaffolding looks similar.
Verification: helper tests plus an isolated execution of the remote bootstrap with
temporary data; conflict, interrupted-publication and retry paths. Rollback:
restore prior helpers and retain existing packages/receipts.

### 8. Improve docstrings where they help operation (low risk, incremental)

An AST inventory found 102 of 191 Python files without a module docstring. That
count includes tests and package initializers; it is not 102 actionable defects.
Some files have comments or function docstrings instead. Prioritize executable
setup/import/migration programs, configuration, routes and complex services.

Action: document purpose, invocation and side effects when reviewing each area.
Keep inline comments focused on reasons and constraints. Do not mass-insert
boilerplate or change historical migrations merely to meet a numeric target.
Verification: compare prose against code; parse changed Python without running
mutating scripts. Rollback: documentation-only revert.

## Performance and file retention

No performance bottleneck has been established. Before optimizing, measure local
math search/rendering, map startup and music querying with representative data;
separate browser/network time from server/database time. Generated city/region
reference files are large but are data, not automatically modularization targets.

No file is approved for deletion by this report. In particular, the compatibility
helper is used, the older Spotify implementation remains imported, and `dist`
contains active workflow state. A later retention inventory should record paths,
sizes, purpose, last use evidence, authoritative copies and restoration needs.
No changes to environments, backups or database layout are recommended as an
incidental side effect of code cleanup.

## Recommended first implementation batch

1. Documentation index and pointers added in this documentation batch; review
   their links before committing.
2. Review the tracked backup's purpose and preservation plan separately.
3. Choose one small code change next: separate shared music catalog behavior from
   historical publishing. Keep all existing behavior until tests justify removal.
4. Keep mathematics low priority in light of its prior refactoring. Review history
   and establish a concrete problem before planning any further extraction.
   Publishing restructuring also needs import/bootstrap regression coverage first.

This report is ready for review. It does not authorize deletion, certify security,
or assert that performance or scheduled-task health has been verified.
