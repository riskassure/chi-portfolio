# When the site is down: recovery guide

Written 2026-10-30 from four real test runs (see [What was tested](#what-was-tested)).
For one bad entry or a bad live edit, you usually don't need this page: fix the entry,
or restore last night's database ([Nightly backups](NIGHTLY_BACKUPS.md#restore)).

Every command below says which window it goes in:

- **PA console**: pythonanywhere.com, **Consoles** tab, **Bash**. Runs on the server.
- **Laptop PowerShell**: a PowerShell window in `C:\Development\chi-portfolio`.

Pasting a server command into PowerShell fails harmlessly (PowerShell refuses `&&` and
runs nothing), so if you see `The token '&&' is not a valid statement separator`, you
are in the wrong window.

## First: what kind of "down" is it?

| What you see | Most likely cause | Go to |
| --- | --- | --- |
| Every page shows PythonAnywhere's "Something went wrong" or error page, right after you published code (option 14, 15 or 22) | The new code doesn't start | [A. The site won't start](#a-the-site-wont-start) |
| Same error page and you changed nothing | PythonAnywhere itself, or a full disk | Check https://www.pythonanywhere.com/forums/ and status posts, then [A](#a-the-site-wont-start) and [Disk space](#keep-the-disk-from-filling-up) |
| Pages load but content is wrong, missing, or pages error only where the database is used | Bad or damaged database | [B. Bad database](#b-bad-database) |
| The browser can't find the site at all ("can't reach this page", DNS error), but `https://cwoo.pythonanywhere.com` or the PA Web tab is fine | Domain or DNS problem | [C. Domain problem](#c-domain-problem) |
| You can't log in to PythonAnywhere, or the account or its files are gone | Account lost | [D. Rebuild on a new account](#d-rebuild-on-a-new-account) |
| The music page stopped updating | Spotify sign-in refused | [Renewing the Spotify sign-in](../SPOTIFY_RENEWAL.md) |

## A. The site won't start

1. **Read the error log.** Web tab, **Log files**, `www.cwoo.me.error.log`, scroll to the
   bottom. A Python traceback near the time of the reload names the file and line.
   Lines that only say `OSError: write error` are harmless: a visitor (often a bot)
   left before a page finished sending. There are a few every day.
2. **If you just published code,** put back the previous version of the files you
   published. Each publish saved them in `/home/cwoo/backups/before-code-update-<id>/`
   or `before-frontend-update-<id>/` (the newest folder is the one from that publish;
   **PA console**: `ls -td ~/backups/before-*-update-*/ | head -3`). Copy the files back
   to the same places under `/home/cwoo/chi-portfolio/`, then press the green
   **Reload** button on the Web tab. Option 16 retries the reload and homepage check.
3. **If you just ran option 22 (packages),** see
   [Package updates](../deployment/PACKAGE_UPDATES.md) for undoing an update.
4. **If nothing changed,** check disk space ([below](#keep-the-disk-from-filling-up))
   and that the settings file is intact (**PA console**:
   `ls -la ~/.config/chi-portfolio/`; `hosting.json` must exist). The site refuses to
   start without it, by design.

The database is not affected by any of this. Code backups never contain it.

## B. Bad database

Use `restore-live` from the nightly backups: [Nightly backups, Restore](NIGHTLY_BACKUPS.md#restore).
The 2026-10-30 drill (Run 2 below) showed it works as written: the preview shows the
entry counts now and in the backup, `--apply` saves a `before-restore-…db` copy first,
and the whole restore took 6 seconds. Afterwards:

- Reload the web app and look at a few pages.
- Once you're happy, compress the safety copy so it doesn't eat disk space
  (**PA console**: `gzip ~/backups/before-restore-*.db`).
- At home, run option 8.

## C. Domain problem

The site's address is set in two places. Recorded 2026-10-30:

| Where | Setting | Value |
| --- | --- | --- |
| Namecheap (registrar), Domain List, `cwoo.me`, **Advanced DNS** | CNAME record, host `www` | `webapp-3227028.pythonanywhere.com` |
| Namecheap, same page | Bare `cwoo.me` | Namecheap URL redirect to `https://www.cwoo.me` (it answers from `192.64.119.210`) |
| PythonAnywhere Web tab | Web app name | `www.cwoo.me` |
| PythonAnywhere Web tab, Security | HTTPS certificate | Auto-renewing Let's Encrypt; Force HTTPS enabled |

Check what the world sees (**Laptop PowerShell**):

```powershell
nslookup -type=CNAME www.cwoo.me
nslookup cwoo.me
```

The first must answer `canonical name = webapp-3227028.pythonanywhere.com` (or
whatever the Web tab's **DNS setup** line shows now). If not, fix the CNAME at
Namecheap. Changes take from minutes to a few hours to reach everyone. Also check
the domain hasn't expired (Namecheap's Domain List shows the expiry date and
auto-renew).

If the browser warns about the certificate, open the Web tab's Security section; the
Let's Encrypt certificate renews itself but needs the CNAME to be right.

## D. Rebuild on a new account

Only if the PythonAnywhere account or its files are gone. The site is about 40 MB of
files plus a 16 MB database, and every piece has a copy off the server:

| Piece | Where the off-server copy is |
| --- | --- |
| Website files, photos, map data, diagrams, and a database snapshot | Newest full-site archive on the laptop: `%USERPROFILE%\.config\chi-portfolio\backups\full-site\full-site-<date>.zip` |
| A newer database | Newest option 8 snapshot: `Downloads\chi-portfolio\database\<time>\live-snapshot.db` (compare dates with the archive's) |
| Code (to cross-check) | GitHub `main` |
| Admin password and session secret | Not copied anywhere on purpose. You choose a new password during the rebuild |
| Spotify sign-in | Not copied. Renew it after the rebuild ([Spotify renewal](../SPOTIFY_RENEWAL.md)) |
| Esri map key | Laptop `%USERPROFILE%\.config\chi-portfolio\esri-api-key.txt`; upload with option 17 |

Steps (account name `cwoo` below; replace it everywhere if the new account has another
name, including in the helper's settings):

1. **Upload the archive.** Files tab, upload the newest `full-site-<date>.zip` to your
   home folder. Then **PA console**:

   ```bash
   cd ~ && test ! -e chi-portfolio && mkdir chi-portfolio && cd chi-portfolio && unzip -q ~/full-site-*.zip && ls
   ```

   You should see `backend` and `frontend`. If you're using a newer option 8
   snapshot, upload it and copy it over `~/chi-portfolio/backend/portfolio.db` now,
   before the site runs.

2. **Python setup.** **PA console**:

   ```bash
   mkvirtualenv --python=/usr/bin/python3.13 chi-portfolio
   pip install --no-cache-dir -r ~/chi-portfolio/backend/requirements.txt
   ```

3. **Private settings.** The setup script isn't part of the live files, so fetch it from
   GitHub first (the repository is public). **PA console**:

   ```bash
   mkdir -p ~/tools && curl -fsSL -o ~/tools/setup_pythonanywhere.py https://raw.githubusercontent.com/riskassure/chi-portfolio/main/backend/setup_pythonanywhere.py
   ~/.virtualenvs/chi-portfolio/bin/python ~/tools/setup_pythonanywhere.py
   ```

   It asks for a new admin password (16+ characters) and writes
   `~/.config/chi-portfolio/hosting.json`. It sets the site address to
   `https://<account>.pythonanywhere.com`. For the real domain, change it:

   ```bash
   ~/.virtualenvs/chi-portfolio/bin/python -c "import json,pathlib;p=pathlib.Path.home()/'.config/chi-portfolio/hosting.json';d=json.loads(p.read_text());d['PUBLIC_ORIGIN']='https://www.cwoo.me';p.write_text(json.dumps(d))"
   ```

   Without this, admin saves on `www.cwoo.me` fail with "Request origin rejected".

4. **Web tab.** **Add a new web app**, domain `www.cwoo.me`, **Manual configuration**,
   Python 3.13. Then set exactly what the old one had (recorded 2026-10-30):

   | Setting | Value |
   | --- | --- |
   | Source code and Working directory | `/home/cwoo/chi-portfolio` |
   | Virtualenv | `/home/cwoo/.virtualenvs/chi-portfolio` |
   | Static files | none |
   | Force HTTPS | Enabled |
   | Password protection | Disabled |

   Open the WSGI configuration file link (it was `/var/www/www_cwoo_me_wsgi.py`) and
   replace everything in it with these three lines:

   ```python
   import sys
   sys.path.insert(0, '/home/cwoo/chi-portfolio/backend')
   from pythonanywhere_wsgi import application
   ```

   Press **Reload**. Note the new **CNAME** value under DNS setup.

5. **Domain.** At Namecheap, Advanced DNS, set the `www` CNAME to the new
   `webapp-…pythonanywhere.com` value ([C](#c-domain-problem)). When `nslookup` shows it,
   turn on the auto-renewing Let's Encrypt certificate in the Web tab's Security section.

6. **Scheduled tasks.** Tasks tab, two daily tasks (recorded 2026-10-30):

   | Time (UTC) | Command | Description |
   | --- | --- | --- |
   | 10:17 | `/home/cwoo/.virtualenvs/chi-portfolio/bin/python /home/cwoo/chi-portfolio/backend/src/database/nightly_backup.py backup --database /home/cwoo/chi-portfolio/backend/portfolio.db --backups /home/cwoo/backups/nightly` | Nightly live DB backup |
   | 16:30 | `cd /home/cwoo/chi-portfolio/backend/src && SPOTIFY_TOKEN_PATH=/home/cwoo/.config/chi-portfolio/spotify-tokens.json /home/cwoo/.virtualenvs/chi-portfolio/bin/python -m services.music.spotify_top --database /home/cwoo/chi-portfolio/backend/portfolio.db --refresh` | Refresh six-month Spotify top tracks |

7. **Keys.** Esri: helper option 17 from the laptop. Spotify: follow
   [Spotify renewal](../SPOTIFY_RENEWAL.md). SSH for the helper: add the laptop's public
   key to the new account's `~/.ssh/authorized_keys`
   ([Changing the site's secrets](../ROTATING_SECRETS.md)); a new account also needs a new
   API token in the laptop's `pythonanywhere-api.json`.

8. **Check.** Home, biography, resume, music, photos, the map (tiles need the Esri key),
   math search, a math entry with a diagram, admin sign-in. Then run option 8 at home.

Steps 1 to 3 and the page checks were rehearsed on the laptop in Run 3 below; steps 4
to 7 copy the settings recorded from the working account but were not rehearsed on a
second account.

## Keep the recovery copies fresh

- **Monthly, or before big changes: a new full-site archive, downloaded.** This is
  the only off-server copy of the photos, map data and diagrams.

  **PA console** (the archive script isn't among the live files, so fetch it first):

  ```bash
  mkdir -p ~/tools && curl -fsSL -o ~/tools/backup_site.py https://raw.githubusercontent.com/riskassure/chi-portfolio/main/backend/backup_site.py
  cd ~ && D=$(date -u +%Y%m%d)
  (umask 077; ~/.virtualenvs/chi-portfolio/bin/python ~/tools/backup_site.py ~/backups/full-site-$D.zip --root ~/chi-portfolio)
  sha256sum ~/backups/full-site-$D.zip
  ```

  Avoid live edits for the minute it runs. Then **Laptop PowerShell** (use the date the
  server printed):

  ```powershell
  $D = "20261030"
  $Dest = "$env:USERPROFILE\.config\chi-portfolio\backups\full-site"
  New-Item -ItemType Directory -Force $Dest | Out-Null
  scp cwoo@ssh.pythonanywhere.com:backups/full-site-$D.zip "$Dest\"
  Get-FileHash "$Dest\full-site-$D.zip" -Algorithm SHA256
  ```

  The two checksums must match (PowerShell prints capitals; that's fine).
- The laptop copy is still on the laptop. A copy in cloud storage you already use
  would also cover a lost laptop.

### Optional: try an archive on the laptop

What Run 3 did, to confirm an archive really works. **Laptop PowerShell**, after the
download above:

```powershell
$R = "C:\Development\chi-portfolio\dist\rebuild-drill"
Expand-Archive "$Dest\full-site-$D.zip" -DestinationPath $R
python -m venv "$R\.venv"
& "$R\.venv\Scripts\python" -m pip install -r "$R\backend\requirements.txt"
$env:PORTFOLIO_DB_PATH = "$R\backend\portfolio.db"
$env:MATH_DIAGRAM_DIR = "$R\backend\data\math\diagrams"
$env:FLASK_ENV = "development"
Push-Location "$R\backend\src"
& "$R\.venv\Scripts\python" app.py
```

Open `http://127.0.0.1:5000/` (no sign-in; admin login is off in this copy; the map
has no background tiles because the Esri key isn't in the archive). Afterwards:
Ctrl+C, then

```powershell
Pop-Location
Remove-Item Env:PORTFOLIO_DB_PATH, Env:MATH_DIAGRAM_DIR, Env:FLASK_ENV
Remove-Item -Recurse -Force "C:\Development\chi-portfolio\dist\rebuild-drill"
```

Clear those three settings before using option 6 in the same window, or close the
window. Notes: `start_local.py` isn't in the archive (it's a laptop tool), hence
`app.py`. `py -3.13` may say "No suitable Python runtime found"; use `python` from the
project's activated `.venv`. For a real rebuild, use Python 3.13 like the server.

## Keep the disk from filling up

A full disk stops the nightly backup and live saves. On 2026-10-30, `~/backups` held
118 uncompressed 16 MB database copies (1.9 GB): each option 8 run leaves its
`portfolio-<time>-<id>.db` on the server, and each publish leaves a `before-…db`.
Nothing deletes them. Compressing keeps every copy but makes each about 3.4 MB.

**PA console**, now and then (for example after option 8):

```bash
find ~/backups -maxdepth 1 -name '*.db' -mtime +0 -exec gzip {} \;
du -sh ~/backups
```

That took the folder from 1.9 GB to 407 MB. It doesn't touch the nightly, code-backup
or diagram folders. To use a compressed copy: `gunzip -k file.db.gz`. The **Account**
page shows the whole account's disk use against its limit.

## What was tested

All four runs on 2026-10-30, by Chi, with nothing live changed except the Spotify sign-in
(Run 4, intended) and compressing old backups.

| Run | What | Result |
| --- | --- | --- |
| 1 | Recorded the Web tab, tasks, private settings folder, logs, disk use and DNS | Settings above; WSGI file holds only the three import lines; error log holds only harmless `write error` lines; backups compressed 1.9 GB to 407 MB |
| 2 | Extracted the newest nightly backup to `~/drill`, deleted 5 entries (1,252 to 1,247), previewed and applied `restore-live` against that copy | 3 of 3 nightly backups verified; preview 1,252 vs 1,247; restored to 1,252 in 6 s with a `before-restore` copy |
| 3 | New full-site archive on the server, downloaded, unpacked on the laptop, fresh virtualenv, ran the site from it | 20.5 MB archive, checksums matched; all 9 pinned packages installed (on Python 3.14); home, music, photos, map and a diagram entry all worked; map tiles missing (expected) |
| 4 | Spotify sign-in renewal | See [Spotify renewal](../SPOTIFY_RENEWAL.md#what-was-tested) |

Found and fixed in this guide along the way: `backup_site.py` and
`setup_pythonanywhere.py` aren't on the server (fetch them from GitHub);
`start_local.py` isn't in the archive; `setup_pythonanywhere.py` sets the
`pythonanywhere.com` address, not `www.cwoo.me`.

Not tested: a rebuild on a second PythonAnywhere account, a DNS change at Namecheap,
and certificate issuance.
