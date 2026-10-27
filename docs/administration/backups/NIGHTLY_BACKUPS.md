# Nightly backups of the live database

Added 2026-10-27. Script: `backend/src/database/nightly_backup.py` (standard library
only). Tests: `backend/tests/test_nightly_backup.py`.

## Why

The helper and option 8 take a verified backup before they change the live database,
but the live **Save** buttons on the admin pages don't. A nightly backup means a bad
live edit, or a damaged database file, costs at most one day of changes.

## What one run does

1. **Snapshot.** Copies `portfolio.db` with SQLite's online backup API, the same method
   option 8 and publishes use. Unlike copying the file, this gives a consistent copy
   even while the website has the database open: it holds the last committed state,
   never half of a write.
2. **Check.** Runs `PRAGMA integrity_check` on the copy and confirms it is the portfolio
   database (it has the `math_concepts` table).
3. **Compress and verify.** Gzips the copy (16 MB becomes about 3.4 MB), then unzips it
   again in memory and confirms the SHA-256 matches the snapshot exactly.
4. **Keep.** Saves `portfolio-YYYYMMDDTHHMMSSZ.db.gz` plus a small
   `portfolio-YYYYMMDDTHHMMSSZ.json` note (time, checksums, sizes, number of math
   entries) in `/home/cwoo/backups/nightly/`. Times in names are UTC. Files are
   owner-only.
5. **Rotate**, only after step 3 succeeded. Keeps the newest backup of each of the last
   **7 days**, the last **4 weeks** and the last **6 months**: at most 17 files, about
   60 MB at today's size. Older nightly files are deleted.
6. Prints a short JSON report, which appears in the task log.

If any step fails, nothing new is kept, nothing is rotated, and the task log shows the
error. Temporary files start with `.` and are removed; if a run is killed mid-way, the
next run removes leftovers older than a day.

**What rotation can delete:** only files in the nightly folder whose names match
`portfolio-YYYYMMDDTHHMMSSZ.db.gz`, and their `.json` notes. Every other backup in
`/home/cwoo/backups/` (option 8, publishes, `before-live-edit-…`, `before-restore-…`,
full-site archives) is never touched.

## Set it up (once)

### 1. Merge, pull, publish the script

After the pull request is merged, on the laptop: `git pull`, start the helper, choose
**15**, and enter

```
backend/src/database/nightly_backup.py
```

then **3** (stage), **4** (check live), **5** (publish and reload). Option 15 is the
code route; the reload it does is harmless because the website doesn't use this file.

### 2. Try it once by hand

On pythonanywhere.com, open a **Bash console** (Consoles tab) and run:

```bash
/home/cwoo/.virtualenvs/chi-portfolio/bin/python /home/cwoo/chi-portfolio/backend/src/database/nightly_backup.py backup --database /home/cwoo/chi-portfolio/backend/portfolio.db --backups /home/cwoo/backups/nightly
```

You should see `"status": "ok"`, a `"math_concepts"` count matching the site, and
`"folder_mb"` around 3.4. Then check it:

```bash
/home/cwoo/.virtualenvs/chi-portfolio/bin/python /home/cwoo/chi-portfolio/backend/src/database/nightly_backup.py check --backups /home/cwoo/backups/nightly
```

It should end with `1 of 1 nightly backups verified.`

### 3. Create the scheduled task

**Tasks** tab, **Scheduled tasks**: frequency **Daily**, time **10:17** (UTC; the Tasks
tab shows times in UTC), command exactly as in step 2's first command. Save.

Any time works, because the online backup is safe while the site runs; choose one when
you're usually not editing (convert 10:17 UTC to your time zone to check it falls at
night, and change it if not).

### 4. Next day

Open the task's log (the log link beside it in the Tasks tab) and confirm a
`"status": "ok"` report. The **Files** tab should show a second file in
`/home/cwoo/backups/nightly/`.

## Checking on it

- **Task log**: each run's report, or the error. Nothing alerts you when a task fails,
  so glance at it now and then, for example when you run option 8.
- **`check` command** (step 2 above): re-verifies every nightly file by unzipping it,
  comparing its checksum with its note, and running the integrity check.
- **Disk use**: the report's `folder_mb` is the nightly folder's size. If it goes above
  200 MB the report adds a `"warning"` line (the run still succeeds). The **Account**
  page on PythonAnywhere shows your whole quota. Other backups in `/home/cwoo/backups/`
  still pile up and are still yours to delete through the Files tab; the biggest are the
  uncompressed 16 MB `portfolio-<time>-<id>.db` copies each option 8 leaves there.

To keep a different number of backups, add `--keep-daily N`, `--keep-weekly N` or
`--keep-monthly N` to the task's command.

## Restore

Restoring puts the whole database back as it was at that night's backup. **Every live
edit made since then is undone** (they stay in the safety copy, see below). For one
bad entry, editing the entry back is usually simpler; to see an old version first, use
`extract` below.

### Look at a backup without touching anything

Decompress one into a new file and verify it (works on the server or the laptop; it
refuses to overwrite an existing file):

```bash
/home/cwoo/.virtualenvs/chi-portfolio/bin/python /home/cwoo/chi-portfolio/backend/src/database/nightly_backup.py extract /home/cwoo/backups/nightly/portfolio-20261028T101700Z.db.gz --output /home/cwoo/backups/look-20261028.db
```

On the laptop, download the `.db.gz` (and its `.json`) through the Files tab first, then
run the same command with `python backend/src/database/nightly_backup.py` and local
paths. Open the result with `sqlite3` or a DB browser.

### Put a backup back into the live site

1. **Preview** (changes nothing; shows the number of math entries now and in the backup):

   ```bash
   /home/cwoo/.virtualenvs/chi-portfolio/bin/python /home/cwoo/chi-portfolio/backend/src/database/nightly_backup.py restore-live /home/cwoo/backups/nightly/portfolio-20261028T101700Z.db.gz --database /home/cwoo/chi-portfolio/backend/portfolio.db --backups /home/cwoo/backups
   ```

2. **Restore**: run the same command with `--apply` added at the end. It first saves a
   verified copy of the current live database as
   `/home/cwoo/backups/before-restore-<time>-<id>.db` (rotation never deletes it), then
   copies the backup into the live database with the SQLite backup API. That writes
   inside the open database under SQLite's own locking, so visitors see either the old
   or the restored database, never a mix; you don't need to stop the site. It finishes
   with an integrity check. To undo a restore, restore from the before-restore copy
   (gzip it first: `gzip -k` on the file, then use the `.db.gz`).
3. **Reload** the web app (Web tab, green button) and look at a few pages.
4. **At home, run option 8.** The laptop's last sync point no longer matches the live
   site, so option 8 will treat the restored content as live changes and bring them
   home. If you had unpublished laptop edits, it may refuse; follow
   [If option 8 refuses](../CHANGE_STEPS.md#if-option-8-refuses).

Restoring a file by copying it over `portfolio.db` (Files tab or `cp`) is **not** safe
while the site runs; use `restore-live`.

## Copies off the server

These backups live on the same PythonAnywhere account as the site. They protect
against bad edits and a damaged database. They don't protect against losing the
account or the disk. Your off-server copies today:

- Each **option 8** run downloads a verified live snapshot to the laptop
  (`Downloads\chi-portfolio\database\<time>\live-snapshot.db`). That is as recent
  as your last option 8, which can be weeks.
- The full-site archive of 2026-10-18 on the laptop (see
  [BACKUP_RECOVERY.md](BACKUP_RECOVERY.md)).

That is probably enough for a personal site. If you want more, download the newest
nightly `.db.gz` through the Files tab once a month and run `extract` on it locally to
verify it; it's 3–4 MB. Neither copy is off the laptop; a copy in cloud storage you
already use would cover a lost laptop too.

## Spotify files

Not included, on purpose. If the Spotify job runs on the server, what it produces
(the published ranking) is in `portfolio.db`, which is backed up. Beside the token, it
keeps only `spotify-top-jobs.db`, a one-row record of the last run and retry time; if
lost, the next run simply refreshes. The token file is a credential and shouldn't be
copied into backups; if lost, reconnect Spotify. The listening-history database
(`spotify-history.db`) exists only on the laptop.
