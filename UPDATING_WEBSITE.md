# Updating the live website

The live database at `/home/cwoo/chi-portfolio/backend/portfolio.db` is the
authoritative content database. A Git push does not update PythonAnywhere.
Never unpack the first-deployment ZIP over the live site.

## Routine code, design, biography and resume updates

1. Make and review changes locally. Run the tests using Python 3.13:

   ```powershell
   .venv313\Scripts\python.exe -m unittest discover -s backend/tests -q
   .venv313\Scripts\python.exe backend/build_deployment_package.py --code-only --output dist/code-update-YYYYMMDD.zip
   ```

   Use a unique date/release name; the builder refuses to replace an archive.
   This package excludes the database, frontend/images and generated diagrams.
   Commit reviewed changes when ready and record the commit with the release.

2. Upload the ZIP through Files to `/home/cwoo/`. Extract into a NEW staging
   directory, not the live directory. In a Bash console:

   ```bash
   workon chi-portfolio
   cd /home/cwoo
   mkdir review-YYYYMMDD
   unzip code-update-YYYYMMDD.zip -d review-YYYYMMDD
   ```

3. Pause admin edits and imports until verification is complete. Check your disk
   quota; allow room for the backup and staging files. Back up BEFORE copying:

   ```bash
   python /home/cwoo/review-YYYYMMDD/chi-portfolio/backend/backup_site.py --root /home/cwoo/chi-portfolio /home/cwoo/backups/site-YYYYMMDD.zip
   ```

   Download this private backup through Files and retain it on your laptop.
   It includes code, frontend media, generated diagrams and a SQLite snapshot.
   It excludes raw import folders, private hosting settings and the virtualenv.
   Keep hosting settings separately in a private backup; never post them in chat.

4. Review the staged manifest and changed files. This procedure is for code-only
   changes with unchanged dependencies and database schema. If requirements,
   schema, removed files, or media changed, stop and prepare a specific migration
   and rollback plan. Do not run historical migrations in bulk.

5. For an ordinary code-only release, copy the staged files, preserving live data:

   ```bash
   cp -r /home/cwoo/review-YYYYMMDD/chi-portfolio/. /home/cwoo/chi-portfolio/
   cd /home/cwoo/chi-portfolio
   python -m unittest discover -s backend/tests -q
   ```

   Use this command ONLY with a package built with `--code-only`. Existing files
   absent from the archive are retained. The copy is not atomic: use a quiet
   period and avoid admin work while it runs. Reload the application in Web only
   after tests pass. If tests fail, roll back the changed code before reloading.

6. Check home, biography, resume, music, photos, math search, equations, a diagram,
   and admin login/logout. Inspect the PythonAnywhere error log if needed. Resume
   editing only after checks pass. Record the date, commit and backup filename.
   Delete the uploaded update ZIP and staging directory through Files after
   verification; retain the latest working backup privately and monitor quota.

## Math, music, photographs and other database content

- Small math edits: use the live admin editor after taking a backup.
- Locally prepared content: download a fresh live database snapshot first and
  work on a separate local copy, leaving your existing local database intact.
- Publish with a reviewed, narrowly scoped migration for only the intended
  records, checking whether those records changed since the snapshot. Include
  associated new media/diagrams and validate links. Back up immediately before
  applying it. Pause live edits during this process.
- Do not replace the entire live database with the laptop database. Music/photo
  imports likewise need a reviewed data-and-assets transfer, not a code ZIP.

Content merging is not automated by these tools; prepare each migration with
its own validation and rollback steps.

## Rollback

For a code-only update, extract the saved backup into a separate recovery folder
and copy back ONLY the files changed by that release; remove only newly added
code files listed in its manifest. Keep the current database and media. Reload
and repeat the browser checks. Do not blindly copy the whole backup over the site.

For a failed content/schema migration, stop writes and prepare a recovery plan
before restoring a database. A full database restore discards edits made after
the backup. Preserve a snapshot of the current database first. Restore while
the web application is disabled/stopped, accounting for SQLite WAL/SHM files;
do not replace an open SQLite database. Re-enable/reload and verify afterwards.

## Custom domain

The update procedure stays the same after changing the domain. The domain switch
is a separate release: update DNS, HTTPS and the private `PUBLIC_ORIGIN` setting,
then test login, logout and edits at the new address. Keep credentials private.
