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
See the [admin runbook](../../docs/ADMIN_RUNBOOK.md) for starting and refreshing
local copies. A local save writes the selected working database, not production.
The math creation route can also accept authenticated production edits; this guide
intentionally uses the local workflow to allow review before publication. Always
check the browser's address before pressing Create Concept.

### 2. Fill in the entry (field guidance for either workflow)

| Editor field | Guidance |
| --- | --- |
| Title | Clear mathematical name; required. The server derives the canonical name and URL slug from it. Review the resulting URL after saving. |
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

If creation reports a canonical-name or slug conflict, search the existing entries
and resolve the overlap rather than repeatedly submitting. If a request is
interrupted, check whether the entry exists before creating it again. A success
message does not replace checking diagram/rendering diagnostics.

### 4. Publish a new text/equation entry

In the helper:

1. **1** lists supported math differences from the unchanged baseline.
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

**Scope limit:** the current helper's new-entry publisher supports text/equations,
not asset transfer or server-side diagram generation. PSTricks, included images,
TikZ/figure content and other blocked media require a separately reviewed
publication plan. Do not use a frontend-file upload or replace the live database
to bypass that limit. A diagram working locally does not establish publishability.

Git commit/push does not publish database entries. Do not add working databases to
Git. Keep the helper's review, receipt and backup references. Detailed technical
publication procedures are in [MATH_SYNC.md](../../MATH_SYNC.md).

## B. Production first: create live, then synchronize locally

Use this when the content is ready to be public immediately. Unlike the local
helper publication, the production editor has no separate staging or approval
step and its creation route does not automatically take a backup.

1. Prepare a fresh production database backup before editing. In a PythonAnywhere
   Bash console, use the existing backup tool below with a new, descriptive
   filename. Replace `UNIQUE-NAME` and wait for ?Database snapshot created.?
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
- [README.md](README.md): frontend architecture and rendering dependencies.
- [ALGEBRA_DEFINITION_AUDIT.md](ALGEBRA_DEFINITION_AUDIT.md) and
  [CATEGORY_DEFINITION_AUDIT.md](CATEGORY_DEFINITION_AUDIT.md): topic-specific audit notes,
  not the general entry-creation workflow.

No production writes or sample entries were used to verify this documentation.
