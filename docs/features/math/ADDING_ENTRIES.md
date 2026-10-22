# Add a new mathematics entry

Checked against `create.html`, `math_editor.js`, the concept-creation route/service,
and the website helper on October 21, 2026. This guide describes the recommended
local-first workflow and the alternative production-first workflow. It does not
create an entry. Production-first behavior is documented from source inspection,
not verified by creating a live test entry.

| Choice | Where Create Concept saves | When visitors can see it | Next synchronization |
| --- | --- | --- | --- |
| Local first (recommended) | Helper-selected local working database | After reviewed helper publication | Publish selected entry, then refresh locally with option 8 |
| Production first | Live production database | Immediately after a successful save | Bring live changes home with option 8; do not republish the entry |

There is no automatic two-way synchronization. Git and the helper solve different
problems; see the synchronization and commit guidance below.

## A. Local first: create, review, then publish

### 1. Prepare the local working copy

1. Open the website helper from the project directory:
   `python backend/website_workflow.py`.
2. Check the working database path shown in its menu. If it is out of date, stop
   the local server and use option **8** to bring website changes home first.
   Read its comparison result; do not discard unpublished edits or edit the baseline.
3. Choose **6** to start the local website using that working database.
4. Sign in at `http://127.0.0.1:5001/admin_dashboard.html` with your local admin
   password, then open `http://127.0.0.1:5001/math/create.html`.
5. Search the existing collection for the proposed title and common alternate
   names before creating a duplicate. An existing entry may only need a synonym
   or a revision instead.

Keep the server terminal open. Use a second helper terminal when ready to publish.
See the [admin runbook](../../ADMIN_RUNBOOK.md) for starting and refreshing
local copies. A local save writes the selected working database, not production.
The math creation route can also accept authenticated production edits; this guide
intentionally uses the local workflow to allow review before publication. Always
check the browser's address before pressing Create Concept.

### 2. Fill in the entry (field guidance for either workflow)

| Editor field | Guidance |
| --- | --- |
| Title | Clear mathematical name; required. The server refuses a title that is already another entry's title, synonym or defined term (ignoring capitals), as publication would; review that entry first. |
| URL slug | Filled in from the title as lowercase words joined by hyphens: accents become plain letters, apostrophes are dropped and other punctuation becomes a hyphen (`Euler's theorem` gives `eulers-theorem`). You can shorten it, as many existing entries do. The canonical name is built from it (`eulers-theorem` gives `EulersTheorem`). Check *Slug preview* before Create Concept: the slug and canonical name can't be changed after saving. The server refuses a slug that isn't lowercase words joined by hyphens, or one already used by another entry. |
| Owner | Entry author/owner; defaults to `CWoo` if blank. |
| Classifications | Select appropriate existing MSC classifications using the suggestions. Choose at least one for helper publication. |
| Document Types | Select appropriate existing types, such as Definition, Theorem, Proof or Example. At least one is required for helper publication. An entry may have several. |
| Synonyms | Optional alternate names for this same concept, comma-separated. Avoid ambiguous words that would create misleading automatic links. |
| Other Concepts Defined Here | Optional additional terms substantially defined in this entry, comma-separated; not merely words mentioned in passing. |
| Related Concepts | Optional links to existing concepts selected through the picker. Publication checks that those targets exist in the live database. |
| LaTeX Body | Required source text (`cleaned_tex`), including explanatory prose and mathematical notation. |
| Cleaned/reviewed checkbox | Reflect the actual editorial state; it is not a substitute for previewing and checking the entry. |

The editor requires title and body, but the publication helper imposes additional
checks, including classifications, document types and valid identifiers. A local
save is therefore not proof that an entry is ready to publish.

Follow [AUTHORING_STANDARDS.md](AUTHORING_STANDARDS.md) for the authoritative
notation, section, proof, document-type and linking conventions. In particular:

- Use `\(...\)` inline and `\[...\]` for display mathematics in new text.
- Use formal definition/theorem/proof environments where appropriate.
- Introduce notation and check hypotheses, examples and sources for accuracy.
- Keep necessary local macro definitions at the beginning; do not redefine shared
  macros or manually edit stored `rendered_tex`.
- Review automatic links for ordinary-language words with mathematical meanings.

For example, a short source draft might contain an introductory sentence followed
by `\begin{definition} ... \end{definition}` and an example. Replace placeholders
with reviewed mathematical content before saving; the editor is not an accuracy
checker.

### 3. Preview and save locally

1. Choose **Render Preview**. This does not save the concept record; diagram
   preview operations may generate temporary/output assets.
2. Check equations, lists, formal sections, links and any diagram warnings. Edit
   the source and preview again after changes.
3. Choose **Create Concept** once ready. This saves the entry and metadata to the
   selected local database and generates its rendered output.
4. On the resulting concept page, check the actual rendered text and URL. Search
   for the new title and inspect classifications/related links. Use the MathJax
   audit page (`mathjax_audit.html`) for rendering review where needed.

If creation reports that a title, slug or canonical name is already used, the
message names the entry using it. Check whether that entry already covers the concept;
if not, choose a different slug. If a request is
interrupted, check whether the entry exists before creating it again. A success
message does not replace checking diagram/rendering diagnostics.

### 4. Publish a new text/equation entry

In the helper:

1. **1** lists math differences from the unchanged baseline. Anything option 2
   would refuse is marked `[unsupported]` with a `Why:` line, for example a slug
   the publisher rejects or content containing diagrams.
2. **2** prepares the new entry you select. Review its text and all metadata.
3. **3** stages the reviewed package.
4. **4** checks the live database for conflicts and missing metadata/targets.
5. **5**, then `PUBLISH`, adds the reviewed entry with a backup and repeated checks.
6. Verify the public concept page, search, classification listing and links.
7. Stop the local server, choose **8** to refresh the baseline/working copy, then
   **6** to resume local work. Read any reconciliation warning before proceeding.

Preparation and publication reject duplicate titles/canonical names/slugs and
check titles against existing synonyms/defined terms. A related concept created
only locally cannot be assumed to exist on production; publish dependencies in
an appropriate order and recheck conflicts.

**Scope limit:** the helper publishes new entries with text, equations and PSTricks
diagrams. Diagrams go through the diagram route, with SVGs rendered on your laptop,
never on the server. Included images, TikZ/figure content and other blocked media
require a separately reviewed publication plan. Do not use a frontend-file upload or replace the live database
to bypass that limit. A diagram working locally does not establish publishability.

Git commit/push does not publish database entries. Do not add working databases to
Git. Keep the helper's review, receipt and backup references. Detailed technical
publication procedures are in [Content synchronization](../../administration/deployment/CONTENT_SYNC.md).

## B. Production first: create live, then synchronize locally

Use this when the content is ready to be public immediately. Unlike the local
helper publication, the production editor has no separate staging or approval
step and its creation route does not automatically take a backup.

1. Prepare a fresh production database backup before editing. In a PythonAnywhere
   Bash console, use the existing backup tool below with a new, descriptive
   filename. Replace `UNIQUE-NAME` and wait for `Database snapshot created.`
   The destination must not already exist; do not overwrite older backups.

   ```bash
   /home/cwoo/.virtualenvs/chi-portfolio/bin/python /home/cwoo/chi-portfolio/backend/backup_database.py /home/cwoo/backups/before-math-create-UNIQUE-NAME.db --source /home/cwoo/chi-portfolio/backend/portfolio.db
   ```

2. Sign in at `https://www.cwoo.me/admin_dashboard.html` with the production
   website admin password, then open `https://www.cwoo.me/math/create.html`.
   This password is distinct from your hosting login and may differ from local.
3. Search for duplicates and fill in the fields using section A's field guidance
   and the authoring standards. Classifications and document types remain useful
   even though direct creation has fewer checks than helper publication.
4. Use **Render Preview** and review the content before saving. Do not assume
   hosting has the LaTeX/PSTricks tools available on your laptop. Entries requiring
   generated diagrams or new media need a separate reviewed assets/recovery plan;
   a database-only backup does not preserve those files.
5. Press **Create Concept** only when ready for visitors to see the entry. This
   writes directly to the live database; no Git push, helper publish or site reload
   is needed. Check the resulting public page, search and links while logged out.
6. Stop the local server. On your computer, run helper option **8**, inspect its
   comparison result, and restart with **6** after a successful refresh. Search
   locally for the new entry to confirm it arrived.

Do not create the same entry locally and then publish it again. If a live save
was interrupted, search production before retrying. Duplicate-name checks in the
helper are stricter than the direct editor; inspect synonyms and defined terms
before adding a live concept. Retain the pre-edit backup until verification and
synchronization are complete.

## Synchronization: what moves and what does not

- **Local to production:** options **2/3/4/5** publish a selected supported math
  change, with live conflict checks and a backup. They do not upload the entire
  working database or publish all local edits together.
- **Production to local:** option **8** downloads a consistent live snapshot and
  checks it against the previous baseline and working copy. When safe, it selects
  a new baseline/working pair and preserves the old copies.
- **Conflicts:** unpublished or divergent local rows, incompatible schemas, or
  unsupported file-backed changes can block the switch. Read `comparison.json`;
  do not force replacement, edit the baseline, or discard local drafts. Resolve
  individual differences first, then retry. This is not a general automatic merge.
- **Files:** option 8 verifies gallery photos, but does not synchronize source
  code, all media, or math diagram assets. New diagram/file-backed changes may
  require a separate transfer and reconciliation plan.
- **No database swapping:** never upload the entire laptop database to make the
  sites match. It could overwrite newer music, photo, profile or math content.

## Existing-entry document types and diagram publication gaps

Document types can be changed in the authenticated math editor
(`math/edit.html?id=ENTRY-ID`), which sends `types` to the existing update route.
However, the publication helper only supports source-text and synonym changes
for existing entries. A local document-type change is detected as unsupported;
there is currently no reviewed helper publication path for it.

Content and synonym edits to existing entries are allowed when every diagram,
image and embed stays byte-identical and each PSTricks diagram already has a
stored SVG. Missing classifications or types and duplicate unchanged metadata do
not block them. Edits that add, remove or change an image or embed are refused.
Edits that change PSTricks diagrams, and entries whose diagrams have no stored
SVG, go through the diagram route: option 19 renders the SVGs on your laptop, and
options 2 to 5 publish them with the entry.
Option 1 marks refused edits `[unsupported]` and gives the reason. See
[Entries the helper cannot publish](../../administration/deployment/CONTENT_SYNC.md#entries-the-helper-cannot-publish)
for the rules and for which of those edits production-first can and cannot cover.

For a deliberate production-first type correction, take the fresh backup described
in section B, open the existing entry's editor on production, preserve its other
fields, change Document Types and save. Verify the entry while logged out, then
stop the local server and use **8** to bring it home. Resolve any unpublished local
changes before doing this; do not duplicate a local metadata edit on production
and assume the refresh will merge it. This route is confirmed from the editor,
update route and metadata service, not a live write test. If local-first review is
required, defer the edit until a metadata publisher is implemented. This
metadata-only route does not extend to edits that change or add diagrams or
images. Publish diagram changes through the diagram route from your local copy;
image files still have no supported route.

**Diagram publication** works for PSTricks (`pspicture` and `\pstree`). The SVGs
are rendered on your laptop, checked, and published with the entry. The server
places the files before any row changes, keeps a journal, and never runs LaTeX.
See [Publish a diagram change](../../administration/deployment/CONTENT_SYNC.md#publish-a-diagram-change)
for the steps, interruption recovery and cleanup. `\includegraphics` images,
TikZ and other media still have no publication route.

## Migration scripts (historical bulk route)

The scripts in `backend/src/database/math/migrations/` added most of the
September 2026 entries, before the helper existed. Treat them as a record of
what was done, not as a way to add entries. Use the helper instead. Do not
run them in bulk or in order. Many of them check the content as it was then.

Most of them also change existing entries: they edit text and add related
links, synonyms and defined terms. The helper can't publish those changes, so
re-running a script leaves the working copy different from the live site in a
way options 2 to 5 can't fix. The [migration scripts review](../../maintenance/history/MIGRATION_SCRIPTS_REVIEW.md)
lists what each script changes.

If you do need to reuse one, plan that run on its own and review it first.
Apply it only to the local working database, with nothing else writing to it:
stop the local server you started with option 6, and don't run the helper or
another script at the same time. Never apply a migration to the live database. Each script has
these safeguards:

- **`--db` is required.** There is no default. The old default,
  `backend/portfolio.db`, is a stale copy. The path must be an existing math
  database, and a mistyped path is refused without creating a file.
- **It previews by default.** The script takes a snapshot of the database,
  runs against a second copy, and compares the two. It lists the new entries
  and every existing entry it would change. Nothing is written to the database
  you named, and edits made to it meanwhile aren't reported as the script's.
- **`--apply` backs up first.** It writes a verified backup to a `backups`
  folder next to the database, prints the backup path, and then makes the
  change. If the script fails, it prints the backup path again. Four scripts
  commit in stages, so don't assume nothing changed.

If a run fails, recover carefully. Restoring the backup replaces the whole
database, so it also throws away anything saved to it after the backup was
taken, not just the script's changes:

1. Stop everything that writes to the database: the local server, the helper
   and any other script.
2. Check for changes made since the backup. This lists every difference
   between the backup and the database now:

   ```text
   python backend/src/database/math/migrations/migration_db.py PATH-TO-BACKUP PATH-TO-WORKING-DB
   ```

   Compare it with the preview you ran before applying. If every difference is
   one the preview listed, nothing else changed, and you can restore the backup
   by copying it over the database while everything is still stopped.
3. If something else changed too, don't restore over it. Keep the current
   database, and either reverse the script's changes by hand or copy the
   unrelated edits into the restored copy first.

```text
python backend/src/database/math/migrations/SCRIPT.py --db PATH-TO-WORKING-DB
python backend/src/database/math/migrations/SCRIPT.py --db PATH-TO-WORKING-DB --apply
```

`backfill_local_macro_preludes.py` keeps its own dry run and backup, and also
requires `--db`.

## When to commit and push

| What changed? | Git action | How it reaches production |
| --- | --- | --- |
| Only an entry saved in the local database | No Git commit is required for that database save | Reviewed helper publication, then option 8 |
| Only an entry saved on production | No Git commit is required for that database save | Already live; option 8 brings it home |
| Tracked code, templates, shared macros, documentation, or approved source assets | Review/test, then commit and push a focused change | Code/frontend changes still need a separate reviewed deployment; documentation alone normally does not |
| A reusable import/migration script or retained authoring source file | Review and commit the source if intentionally part of the project | Running it is a separate data-changing operation; follow its specific review and backup plan |

For entry-related code changes, commit and push the tested code before deploying
it. Deploy any required rendering support before publishing content that depends
on it. After verification, update and commit operational notes when workflows or
recovery instructions changed. Do not make an empty commit merely because a
content record changed.

Database files, snapshots, credentials and private review packages stay out of
Git. Do not force-add ignored files. Git pull/push synchronizes tracked files,
not database entries, live credentials or helper-selected local copies.

## What the other math documents cover

- [AUTHORING_STANDARDS.md](AUTHORING_STANDARDS.md): writing, notation, structure and review conventions.
- [Math frontend](FRONTEND.md): frontend architecture and rendering dependencies.
- [ALGEBRA_DEFINITION_AUDIT.md](../../maintenance/history/ALGEBRA_DEFINITION_AUDIT.md) and
  [CATEGORY_DEFINITION_AUDIT.md](../../maintenance/history/CATEGORY_DEFINITION_AUDIT.md): topic-specific audit notes,
  not the general entry-creation workflow.

No production writes or sample entries were used to verify this documentation.
