# Making a change: on the road or at home

Which changes you can make from anywhere, which wait until you're at the laptop, and
the order of steps for each kind of change: where to edit, how it is published, when
git is involved, and when to bring the live data home. Checked against the code
(`backend/src/routes/`, `backend/bring_changes_home.py`, `backend/photo_home.py`) on
2026-10-26. The detailed procedures stay in the [admin runbook](../ADMIN_RUNBOOK.md)
and the guides it links to; this page tells you which one to follow and in what order.

## Doing it yourself: where each checklist is

Every task below has a numbered checklist you can follow without help. Run
everything from the project folder `C:\Development\chi-portfolio` in PowerShell.

| Task | Checklist | Notes |
| --- | --- | --- |
| Edit an existing math entry's text (at home) | [Example below](#example-editing-a-math-entry-at-home) | One entry per round of 2-5; option 8 once at the end |
| Edit an existing math entry (on the road) | [Example below](#example-editing-a-math-entry-on-the-road) | Also the only route for title, classification, type, defined-term and related-concept fixes |
| Add one new entry | [Adding a math entry, section A](../features/math/ADDING_ENTRIES.md#a-local-first-create-review-then-publish) | Section B is the live-site route |
| Publish a diagram change | [Publish a diagram change](deployment/CONTENT_SYNC.md#publish-a-diagram-change) | Option 19, then 1 and 2 |
| Add many entries at once | [Runbook: option 20](../ADMIN_RUNBOOK.md#add-many-new-entries-at-once-option-20) | Publishing is self-service. Writing its migration is the hard part: see [Recording a batch yourself](#recording-a-batch-yourself) |
| Merge two entries | [Runbook: option 21](../ADMIN_RUNBOOK.md#merge-two-entries-option-21) | The migration is generated for you (`math_entry_merge.py --write`) |
| Photo title, location, coordinates | [Updating existing photo details](deployment/CONTENT_SYNC.md#updating-existing-photo-details) | Option 12 |
| Biography or resume | [Biography and resume updates](deployment/CONTENT_SYNC.md#biography-and-resume-updates) | Option 9 |
| Travel map | [Runbook: Travel and photography](../ADMIN_RUNBOOK.md#travel-and-photography) | Option 14 with `geography/places-data.js` |
| Frontend or Python change | [Code changes with git](#code-changes-with-git) below, then [option 14](deployment/CONTENT_SYNC.md#publishing-frontend-files-option-14) or [option 15](deployment/CONTENT_SYNC.md#python-and-matching-frontend-deployments-options-15-and-16) | |
| Bring live data home | [Runbook: Bring database changes home](../ADMIN_RUNBOOK.md#bring-database-changes-home) | When it refuses: [If option 8 refuses](#if-option-8-refuses) |
| Check a live page | [How the website works: caching](HOW_THE_SITE_WORKS.md#browser-caching-why-a-page-can-look-unchanged) | Private window, logged out; Ctrl+F5 |

What these checklists don't replace is the mathematical writing itself (drafting
entries and proofs, finding which concepts are missing) and judging wrong automatic
links. Those follow the [authoring standards](../features/math/AUTHORING_STANDARDS.md)
and the local preview.

## The two ways to change the site

| | On the road | At home |
| --- | --- | --- |
| Tool | Any browser, signed in at `https://www.cwoo.me/admin_dashboard.html` | The laptop: the helper (`python backend/website_workflow.py`), the local server (option **6**), git |
| What it changes | Rows in the live database, and only through the edit buttons on the live pages | Anything: data, frontend files, Python code, the database schema, media |
| How a change goes live | Immediately, when you press Save. No review, no package, no reload | Only when you publish it with the helper (options 2-5, 9, 11-15, 18-21) |
| Backup | None automatic (see [Backups for live edits](#backups-for-live-edits)) | The helper takes a server backup before every publish |
| Reaches the laptop | Next time you run option **8** at home | Already there (it started there) |

In short: **on the road you can change data, at home you can change anything.**
A live edit is a database write and nothing else, so it can't change code, page
layout, images or files.

Pushing to GitHub is possible from anywhere, but it never changes the website. Code
merged on the road waits on GitHub until you `git pull` on the laptop and publish it.

## What you can edit on the live site

Only these pages have edit buttons that work on the live site. Each saves straight
into the live database.

| Live page | What you can change | What you can't change there |
| --- | --- | --- |
| Math: `math/create.html`, `math/edit.html?id=<id>` | Create an entry; edit an entry's title, body (TeX), classifications, document types, synonyms, defined terms and related concepts | Slug and canonical name (fixed once saved); deleting; anything about a retired entry; merges and retirements (option 21); diagrams and images (see below) |
| Photography gallery | An existing photo's title, location and coordinates (**Save Details**) | New photos, removing photos, gallery display count, Google Photos import |
| Biography and resume | The page's text fields | Layout, links, PDFs, photos |
| Music | Genre, composition, track name, composer, performer | Nothing else; see [Music details](#music-details) for why these are edited live only |

Math diagrams: the live editor accepts an edit that changes a PSTricks block
(`pspicture`, `\pstree`), but it would render the diagram on the server, which gives
different output from the laptop's SVGs. Only make text edits that leave every
PSTricks block and every `\includegraphics` line exactly as they are, and check the
live page for "[Diagram unavailable]". The rules are in
[Entries the helper cannot publish](deployment/CONTENT_SYNC.md#entries-the-helper-cannot-publish).

## What waits until you're home

These need the laptop: the helper, the SSH key and the PythonAnywhere API token live
only there.

- The travel map, city checklist and regions (the server refuses map edits except
  from `127.0.0.1` on the laptop).
- Gallery display count; new photos; removing photos; Google Photos import.
- Diagram changes (option **19** renders them on the laptop).
- Adding many entries at once (option **20**) and merging or retiring entries
  (option **21**).
- Any frontend file (HTML, CSS, JavaScript) or Python change (options **14**, **15**).
  You can write and merge the code on GitHub from anywhere; deploying it waits.
- Spotify and Google Photos sign-ins (they only work at `127.0.0.1:5001`).
- Migrations (the git records of batches and merges).

## Three rules behind every order of steps

1. **Git doesn't deploy.** Committing and pushing records code; only the helper (or a
   live Save) changes the site. Database content is never in git.
2. **Publishing doesn't need git**, with one exception: after a batch (option 20) or a
   merge or retirement (option 21), record what was published as a migration in a PR.
   A single new entry, a text edit, a photo or a bio change needs no git step.
3. **Option 8 brings live data home, and needs every local edit published first.**
   It compares each table three ways (baseline, working copy, live). If the working
   copy differs from the baseline anywhere in a table, and that isn't already on the
   live site, it refuses for that whole table, not just for the edited entry. So
   option **1** must list nothing before option 8 can switch. Live edits made on the
   road never block it on their own; they just come home.

## Before you leave, and when you get home

**Before leaving (if you expect to edit on the road):** publish every local edit, or
at least note what is unpublished. Run option **8** so the laptop matches live, and
check option **1** lists nothing. Then there is nothing to reconcile later.

**When you get home, before any local editing:**

1. `git pull` (picks up docs or code merged on GitHub while you were away).
2. Stop the local server, run option **8**, type `STOPPED`. Your road edits arrive in
   a fresh working copy.
3. If you merged code on the road, publish it now (options **14** or **15**), then
   check the live page.
4. Start option **6** and work as usual.

If you edit locally first and run option 8 later, your local edits must be published
before option 8 can switch. If a local edit touches an entry you also changed on the
road, the helper's live check (option **4**) will stop it as a conflict: run option 8
first, then redo the local edit on top of the road version.

## Order of steps for each kind of change

"Bring home" means option **8** (stop the local server first, type `STOPPED`).

| Change | 1. Edit where | 2. Publish | 3. Git | 4. Bring home |
| --- | --- | --- | --- | --- |
| Edit an existing math entry, at home | Local editor (**6**, `math/edit.html?id=<id>`) | **1**, **2**, then 3/4/5 | None | Once, after the last publish |
| Edit an existing math entry, on the road | Live `math/edit.html?id=<id>`, after a backup | Saving publishes it | None | When you're home |
| One new math entry, at home | Local `math/create.html` | **2**, then 3/4/5 (**19** first if it has diagrams) | None | Yes |
| One new math entry, on the road | Live `math/create.html`, after a backup | Saving publishes it | None | When you're home |
| Many new entries | Working copy (local editor or a script) | **20** | Migration PR afterwards, then `git pull` | Yes, before the migration |
| Merge or retire entries | Working copy (S's text), plus option 21's session | **2**-5 for S, then **21** and 3/4/5 | Migration PR afterwards, then `git pull` | Yes, after each merge |
| Photo title, location, coordinates, at home | Local gallery, **Save Details** | **12**, then 3/4/5 | None | Yes |
| Photo title, location, coordinates, on the road | Live gallery, **Save Details** | Saving publishes it | None | When you're home |
| Biography or resume text, at home | Local page editor | **9**, then 3/4/5 | None | Yes |
| Music details (live only) | Live music page | Saving publishes it | None | When you're home |
| Biography or resume text, on the road | Live page editor | Saving publishes it | None | When you're home |
| Travel map, cities, regions (home only) | Local map editor | **14** with `geography/places-data.js`, then 3/4/5 | Commit and push the changed file | Not needed (it's a file) |
| Gallery display count (home only) | Local gallery | **18** | Commit and push `gallery-settings.js` | Not needed |
| New photo / remove a photo (home only) | Local import or gallery | **11** / **13**, then 3/4/5 | None | Yes |
| Frontend HTML, CSS, JavaScript (home only) | Repository files | **14**, then 3/4/5 | Commit and push (before or after publishing) | Not needed |
| Python code (home only) | Repository files | **15**, then 3/4/5 | Commit, PR, merge, `git pull` first; publish what was merged | Not needed |
| Documentation | Repository files | Nothing to publish (GitHub shows `main`) | Commit, PR, merge | Not needed |

### Example: editing a math entry at home

1. `git pull`; stop the local server; option **8**; option **1** lists nothing.
2. Option **6**, sign in locally, open `http://127.0.0.1:5001/math/edit.html?id=<id>`,
   edit, **Render Preview**, save. This saves to the laptop's working copy only.
3. Check the local page `math/concept.html?slug=<slug>`.
4. Option **1** shows the entry; option **2** prepares it; **3** stages, **4** checks
   live, **5** and `PUBLISH` publishes with a backup.
5. Check the live page, logged out (a private window).
6. Repeat 2-5 for any other entries. Then stop the server and run option **8** once.
7. No commit: the database isn't in git, and a single edit needs no migration.

Option 2 publishes only the body and synonyms of an existing entry. A change to
title, classifications, types, defined terms or related concepts can't be published
from the laptop; make it on the live site (next example) and bring it home.

### Example: editing a math entry on the road

1. Make a backup (below).
2. Sign in at `https://www.cwoo.me/admin_dashboard.html`, open the entry, and use
   its edit page (`math/edit.html?id=<id>`). Edit, **Render Preview**, save. It is
   live at once.
3. Check the public page logged out (a private window), including any diagrams.
4. At home: `git pull`, stop the local server, option **8**. No commit.

## Code changes with git

The site's code is on GitHub at `riskassure/chi-portfolio`; `main` is the reviewed
version. A code change goes: branch, commit, pull request (PR), merge, pull, publish.

1. `git checkout main`, then `git pull`.
2. `git checkout -b <short-name>` (a branch for this change).
3. Edit the files. Test locally: option **6** (restart it after Python edits), and
   `.\.venv313\Scripts\python.exe -m pytest backend/tests` for Python changes
   (if pytest isn't installed: `-m unittest discover -s backend/tests -q`).
4. `git add <files>`, `git commit -m "What changed and why"`,
   `git push -u origin <short-name>`.
5. On GitHub, open the PR it offers and read the diff. Wait for the test checks
   at the bottom of the PR to turn green ([CI](CI_TESTS.md)), then merge it.
6. On the laptop: `git checkout main`, `git pull`.
7. Publish: option **14** (frontend files only, paths relative to `frontend`) or
   **15** (Python plus matching frontend files, paths relative to the repository),
   then 3/4/5. Check the changed page with Ctrl+F5 or a private window.
8. Changes to the helper itself (`backend/*.py`, not `backend/src`) are not
   published: exit and restart the helper after `git pull`.

Documentation goes the same way, but steps 7 and 8 aren't needed: the admin page's
doc links show GitHub's `main`.

## If option 8 refuses

It says why and names a report, `dist/home-sync/<id>/comparison.json`. Nothing was
changed: your old working copy is still the one in use. Open the report:

| Field | Meaning | What to do |
| --- | --- | --- |
| `blocked` | Tables where the working copy has changes that aren't on live | Option **1** lists unpublished math edits: publish them (2, then 3/4/5), or decide you don't want them. Then run 8 again |
| `photo_conflicts` | Photos edited locally and not published | Option **12**, then 3/4/5 |
| `media_review` | File-backed tables changed on live (for example the Spotify import staging table `stg_spotify_import`) | Rare; review the named table before retrying. Music details no longer appear here |
| `live_changed` | Tables that differ from live | Information only |
| A schema message | The database structure differs | Usually a code rollout step was missed: check the guide for that change |

Never edit the baseline, copy a database over another, or delete the report folder
to get past a refusal.

## Recording a batch yourself

Option 20 publishes a batch on its own, but there is no generator for its git record
yet (unlike merges). To write one by hand:

1. Copy the newest batch migration, such as
   `backend/src/database/math/migrations/add_settheory_entries_20261025.py`, to
   `add_<topic>_entries_<date>.py`.
2. Replace its entries with yours, taking each entry's title, slug, classifications,
   synonyms, defined terms, related slugs and body from the working copy
   (`math_concepts` and its side tables). Set `ORDER` to the live id order shown in
   `dist/math-batches/<batch id>/review.txt`.
3. Run it with `--db <copy of a pre-batch database>` (preview), adjust the escape
   lists until its links match the live entries, then `--apply` on that copy and
   compare the rows with the live snapshot, as in
   [Record a batch in git](deployment/CONTENT_SYNC.md#record-a-batch-in-git).
4. Commit, PR, merge, `git pull`.

Step 3 (matching the automatic links exactly) is the fiddly part. If it's in the way,
the batch is still safely published without it; the migration only lets the
repository rebuild the entries.

## Backups for live edits

The live Save buttons don't take a backup, while the helper does. The
[nightly backup](backups/NIGHTLY_BACKUPS.md) limits the loss to one day's edits, but
before a big math edit on the road it's still worth taking one from a PythonAnywhere
Bash console (log in at pythonanywhere.com in any browser; Consoles tab), using a new
file name each time:

```bash
/home/cwoo/.virtualenvs/chi-portfolio/bin/python /home/cwoo/chi-portfolio/backend/backup_database.py /home/cwoo/backups/before-live-edit-UNIQUE-NAME.db --source /home/cwoo/chi-portfolio/backend/portfolio.db
```

Wait for `Database snapshot created.` Biography and resume saves keep every earlier
revision in the database, so an old version can be recovered without a backup. For a
photo detail edit, note the old title and location before saving.

## Music details

Edit music details (genre, composition, track name, composer, performer) on the
**live** music page, at home or on the road. Option 8 brings them home, as long as
the laptop's music tables still match the baseline (fixed on 2026-10-26).

Don't edit music details in the local preview: there is no helper option to publish
them, and an unpublished local music edit makes option 8 refuse for review. If that
happens, make the same edit on the live site; option 8 accepts it once both sides
match. The daily Spotify ranking is separate: option 8 always takes the live one.
