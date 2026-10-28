# Checking the live site's files against main

`backend/check_live_drift.py` answers one question: **which files on the live
PythonAnywhere site are not what `main` on GitHub says they should be?** It only
reads. It changes nothing on the server, in git or in your working copy, apart from
writing a report under `dist/live-drift/`.

## Why the live files can drift from main

The website is a plain folder of files on PythonAnywhere,
`/home/cwoo/chi-portfolio`. It is not a git checkout: there is no `git pull` on the
server, and the server has no idea what `main` contains. The web server runs the
Python files under `backend/src` and sends the files under `frontend` to visitors'
browsers (see [How the website works](../HOW_THE_SITE_WORKS.md)).

Files reach that folder in three ways:

1. The first deployment unpacked a ZIP of the laptop folder (October 2026).
2. Helper options **14**, **15** and **18** replace individual files with **the
   laptop folder's copy**, whatever branch or uncommitted edit it has. They check
   that the live file has not changed since you reviewed it, but never that the
   laptop's copy matches `main`.
3. Anyone editing in PythonAnywhere's **Files** tab changes the live file directly.
   That edit never comes home, and the next option 14 or 15 for that file shows it
   as a difference and then overwrites it.

So the live site can differ from `main` because of a Files-tab edit, a publish from
a branch or before merging, or a merge that was never published.

## Running it

On the laptop, in the repository folder (PowerShell):

```powershell
git checkout main
git pull
python backend\check_live_drift.py
```

It fetches `origin/main` from GitHub, then connects to
`cwoo@ssh.pythonanywhere.com` with the same SSH key the helper uses (it may ask for
the key's passphrase once). On the server it runs a short read-only Python program
that lists every file in `/home/cwoo/chi-portfolio` with a SHA-256 checksum, and
sends back the text of files that differ. Skipped: `.git`, `__pycache__`, `dist`,
`backend/backups` and virtual-environment folders. Database and archive files are
listed but not read. It takes under a minute.

Options: `--no-fetch` (use the `origin/main` you already have), `--ref <ref>`
(compare with another commit), `--username <account>`.

The console ends with a short summary and the report's path, for example
`dist\live-drift\20261028T213000Z\report.md`. Next to the report:

- `live\...`: copies of the live versions of every changed or extra text file,
  in the same folder layout as the repository.
- `summary.json`: the same classification, for scripts.

## Reading the report

Every file is put in exactly one group. "Site code" means a file the website
actually uses: anything under `backend/src` or `frontend`, plus
`backend/pythonanywhere_wsgi.py`, `backend/serve.py` and `backend/requirements.txt`.

| Section | Meaning | What to do |
| --- | --- | --- |
| **Needs a decision: site code that differs from main** | The live site runs text that is not in `main`. The report shows a diff (`-` lines are main, `+` lines are live). | Decide per file, see below. |
| **Needs a decision: files only on live that git does not ignore** | A file exists only on the server and `.gitignore` does not call it data. | Either it belongs in git (copy from `live\` into the repo, PR), or it is a leftover to delete from the server. |
| Content files that differ or are only on live | Photos, `geography/places-data.js`, `photography/gallery-settings.js`: data the helper publishes as files. | Usually a publish not yet committed. Commit the laptop's copy if it matches live. |
| Other files that differ | Docs, tests, laptop scripts copied at the first deployment. The site never uses them. | Nothing. |
| Same apart from line endings | Windows (CRLF) vs Unix (LF) line ends only. Git on Windows usually checks files out with CRLF, and the helper uploads them as they are. | Nothing; Python and browsers treat both alike. |
| Site code in main that is missing on live | Merged but never published. | Publish with option 14 or 15 if it should be live. |
| Other files in main not on live, data files only on live | Laptop-only tools; databases, diagrams, music data. | Nothing. |

The last section, **The laptop folder**, shows the branch you are on, how far it is
ahead of or behind `main`, and any uncommitted files, because that folder is what
options 14 and 15 publish.

## Deciding about a site code file that differs

Look at the diff and decide which version is right.

- **The live version is right** (for example, a fix made in the Files tab): copy
  `dist\live-drift\<time>\live\<path>` over the same path in the repository, then
  commit, PR, merge, `git pull`. Run the check again: the file should now be "same"
  or "line endings".
- **main is right** (for example, an old experiment left on the server): with the
  laptop on an up-to-date `main`, publish the file with option **14** (frontend
  only) or **15** (Python), then 3, 4, 5. The review shows the same diff in reverse.
- **Neither is complete**: combine them in the repository first, then do both
  steps above.

Never delete a live file without first keeping the copy the report saved under
`live\`.

## When to run it

It was built as a one-time check (step 3 of the improvement plan, October 2026),
but it is safe to run any time, for example after a Files-tab edit or before a
large option 15 publish. A clean result has nothing under either "Needs a decision"
heading.
