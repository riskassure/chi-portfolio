# Changing (rotating) the site's secrets

*Rotating* a secret means replacing it with a new one and making sure the old one
no longer works. This page gives the steps for each secret the site uses, in the
order that avoids locking yourself out. Checked against the code on 2026-10-29.

What each secret is for and where it lives: [Logins and API keys](API_AUTHENTICATION.md).
Never put a secret's value in documentation, git, chat, a screenshot or a command
line (type it at a hidden prompt, or paste it into a private file).

## When to rotate

None of these need rotating on a timer. Rotate one when:

- it may have been seen or copied (pasted into chat, shown on screen, a laptop lost
  or repaired, a file accidentally committed to git);
- someone who knew it should no longer have access;
- it expires (only the Esri key does: **2027-10-13**);
- something odd shows up, such as an admin change you didn't make.

**If you suspect the live site's admin access was used by someone else,** do both
live-site steps at once (new admin password, then new session secret), then check
the live pages and the nightly backups ([Nightly backups](backups/NIGHTLY_BACKUPS.md))
for changes you didn't make.

## Quick reference

| Secret | Where you change it | Signs anyone out? | Also update |
| --- | --- | --- | --- |
| Live admin password | PythonAnywhere Bash console: `hosting_secrets.py password` | No (existing cookies keep working) | Nothing |
| Live session secret | PythonAnywhere Bash console: `hosting_secrets.py session-secret` | Yes, everyone | Nothing |
| Local admin password | Laptop: `start_local.py --reset-password` | Local only | Nothing |
| PythonAnywhere API token | PythonAnywhere Account page, API token tab | No | Laptop `pythonanywhere-api.json` |
| SSH key | New key pair on the laptop | No | Server `authorized_keys`, laptop SSH config |
| PythonAnywhere account password | PythonAnywhere Account page | Your PythonAnywhere browser sessions | Nothing in the helper |
| Spotify tokens | Spotify account, Manage apps | Stops the daily music refresh | Server token copy: [Spotify renewal](SPOTIFY_RENEWAL.md) |
| Google Photos client secret | Google Cloud Console | No | Laptop `google-oauth.json` |
| Google Photos tokens | Google account, third-party access | Laptop import only | Connect again |
| Esri key | ArcGIS developer dashboard | No | Laptop key file, then option 17 |

## Live admin password and session secret

Both live in `/home/cwoo/.config/chi-portfolio/hosting.json` on the server, which
the site reads **only when it starts**. So every change here ends with a reload.

The two are different things:

- The **admin password** is what you type to sign in. Changing it stops new
  sign-ins with the old password. It does **not** sign out a browser that is
  already signed in, because a signed-in browser shows its cookie, not the password.
- The **session secret** (`FLASK_SECRET_KEY`) is what Flask uses to sign the login
  cookie. Changing it makes every existing cookie invalid, so everyone, including
  you, is signed out. It is the only way to cut off a cookie someone may have
  copied; logging out in your own browser can't do that.

**Steps** (in a PythonAnywhere **Bash console**: Dashboard, then Consoles, then Bash):

```bash
workon chi-portfolio                      # use the site's virtualenv (has zxcvbn)
cd ~/chi-portfolio/backend/src
python hosting_secrets.py check           # optional: is the current one weak?
python hosting_secrets.py password        # asks twice, hidden; 16+ characters
python hosting_secrets.py session-secret  # only if you also want everyone signed out
```

Then open the **Web** tab and press **Reload**. Sign in at the live admin page with
the new password to confirm it works.

Good to know:

- The tool never prints a secret. It refuses a password under 16 characters, two
  entries that don't match, or the current password, and then changes nothing.
- It rewrites `hosting.json` in one step, keeping the other settings and the
  owner-only file permissions. If the console is closed halfway, the old file is
  still intact.
- Until you press Reload, the site keeps using the old values.
- If the site fails to start after a reload, the Web tab's error log says why; a
  missing setting appears as "Missing hosting setting". Run the tool again.
- `hosting_secrets.py` reaches the server with option 15 like any other
  `backend/src` file. If it isn't there yet, publish it first (option 15 with
  `backend/src/hosting_secrets.py`, then 3, 4, 5), or edit `hosting.json` by hand in the Files
  tab: replace the value of `ADMIN_PASSWORD`, keep the quotes, save, reload.
- Choose a long random password from a password manager, used nowhere else.

### Checking whether a password is weak

`python hosting_secrets.py check` looks at the current live password and says either
"No common weaknesses found" or "Weak:" with the reasons, without ever showing the
password. `password` runs the same check on a new password and asks you to type
`yes` before saving one that has weaknesses.

The check uses [zxcvbn](https://pypi.org/project/zxcvbn/), a widely used password
strength estimator (a Python port of one Dropbox built). It estimates how many guesses
an attacker would need, knowing tens of thousands of common passwords, English words
and names, keyboard patterns like `qwerty`, dates, repeats, and swaps like `p@ssw0rd`.
The tool also tells it the words tied to this site (`cwoo`, `chi`, `portfolio`,
`admin` and so on) so it counts those as easy guesses. A password counts as weak if it
would take fewer than 10^15 guesses; a random 16-character password or four random
words clears that. When it is weak you see zxcvbn's own warning and suggestions.

What it can't do: no program can tell whether a password was *chosen* randomly, or
whether you use it somewhere else. It only estimates from patterns, so the dependable
route is still a password manager's generator (20+ random characters, or a passphrase
of four or more random words).

zxcvbn is installed in the site's virtualenv from `backend/requirements.txt`. If the
tool says "The zxcvbn package is missing", you ran it without `workon chi-portfolio`,
or the package hasn't been installed there yet: run helper option 22
([Package updates](deployment/PACKAGE_UPDATES.md)), or by hand
`workon chi-portfolio` then `pip install zxcvbn==4.5.0`.

There is no reminder to change the password on a schedule. Current advice (NIST
SP 800-63B) is not to force periodic changes; change it when it is weak, reused,
or may have been seen.

## Local admin password

On the laptop:

```powershell
python backend\start_local.py --reset-password
```

It asks for the new password privately and saves it encrypted for your Windows
account. The local server already makes a fresh session secret every time it
starts, so there is nothing else to rotate locally.

## PythonAnywhere API token

The helper uses it to upload packages and reload the site (options 3, 15, 16).

1. On PythonAnywhere: Account page, **API token** tab, **Create a new API token**.
   The old token stops working immediately.
2. On the laptop, move the old settings file aside (rename
   `%USERPROFILE%\.config\chi-portfolio\pythonanywhere-api.json` to
   `pythonanywhere-api.json.old`).
3. Run `python backend\pythonanywhere_api.py setup` and paste the new token at the
   hidden prompt. It checks the token before saving.
4. Run `python backend\pythonanywhere_api.py check`, then delete the `.old` file.

## SSH key

The laptop signs in to `ssh.pythonanywhere.com` with a key pair (private key on the
laptop, public half on the server). Rotate it by adding a new key **before** removing
the old one, so there is never a moment when neither works.

1. On the laptop, make a new key with a passphrase, in the same private folder:

   ```powershell
   ssh-keygen -t ed25519 -f "$env:USERPROFILE\.config\chi-portfolio\pythonanywhere-ed25519-new"
   ```

   This makes two files: the private key (no extension) and the public half (`.pub`).
2. Add the public half to the server: open `/home/cwoo/.ssh/authorized_keys` in
   the PythonAnywhere Files tab and paste the whole contents of the `.pub` file as a
   **new line**. Keep the old line for now.
3. Point the laptop at the new key: in `%USERPROFILE%\.ssh\config`, change the
   `IdentityFile` line for `ssh.pythonanywhere.com` to the new private key (or load
   the new key into the ssh-agent instead of the old one).
4. Test: `ssh cwoo@ssh.pythonanywhere.com "echo ok"` should print `ok` after asking
   for the new key's passphrase. Then run helper option 4 on any staged package, or
   option 8, as a real check.
5. Only then delete the **old** line from `authorized_keys`, and delete or archive the
   old private key file on the laptop.

If step 4 fails, nothing is lost: the old key still works until step 5.

## PythonAnywhere account password

Change it on PythonAnywhere's Account page. The helper never uses it (it uses the API
token and the SSH key), so nothing else needs updating. Turn on two-factor
authentication there if it isn't already; that matters more than how often you
change the password. The same goes for your GitHub account.

## Spotify

The site stores no Spotify password or client secret, only OAuth tokens that allow
reading your top tracks. To cut them off, remove the app in your Spotify account
(Account, **Manage apps**). Both the laptop and server token copies then stop
working, and the daily music refresh on the server fails safely (the music page keeps
its last list).

Connecting again on the laptop (option 6, then `/api/music/spotify/connect`) gives the
laptop new tokens; copying them to the server and deleting the laptop copy is in
[Renewing the Spotify sign-in](SPOTIFY_RENEWAL.md) (tested 2026-10-30, about 10 minutes).

## Google Photos

Two separate secrets, both laptop only (the live site never talks to Google):

- **Client secret** (in `google-oauth.json`). In Google Cloud Console, open APIs &
  Services, Credentials, then the site's OAuth web client. Use **Add secret**,
  download the client JSON again, save it over
  `%USERPROFILE%\.config\chi-portfolio\google-oauth.json`, connect once to check it
  works, then **disable** and delete the old secret there. Check that the download
  still lists the redirect URI `http://127.0.0.1:5001/auth/google/callback`.
- **Tokens.** Remove the app's access in your Google account (Security, third-party
  connections), delete `%LOCALAPPDATA%\chi-portfolio\google-photos-tokens.json`, and
  connect again before the next import.

## Esri map key

This key is visible to every visitor on purpose, so a copy being seen is expected.
Rotate it before it expires on **2027-10-13**, or sooner if the ArcGIS dashboard shows
usage you don't recognize.

1. In the ArcGIS developer dashboard, create a new key with the **same limits**: basemap
   access only, and referrers limited to this site plus the local addresses.
2. Save it on the laptop to `%USERPROFILE%\.config\chi-portfolio\esri-api-key.txt`.
3. Run helper **option 17** to upload it to the server (it never logs the value).
4. Check the travel map live and locally, then delete the old key in the dashboard.
5. Update the expiry date in this page, [Logins and API keys](API_AUTHENTICATION.md)
   and the runbook.

## How the login limiter decides who is who

The admin sign-in allows five attempts a minute from each visitor, then answers
"Too many login attempts" (HTTP 429). On PythonAnywhere every request arrives at the
site from their **load balancer** (the machine that receives all visitors and hands
requests to the site), so the address the site sees directly is the balancer's,
the same for everyone. Before 2026-10-29 that meant all visitors shared one limit:
someone guessing passwords could also block you for a minute at a time.

The balancer writes the visitor's real address in a request header, `X-Real-IP`
([PythonAnywhere's help page](https://help.pythonanywhere.com/pages/WebAppClientIPAddresses/)).
The site now uses that header, but only when the request really came from a
private-network address (the balancer). A request that reaches the site any other
way keeps its own address, so a visitor can't pick a fresh address for each guess by
writing the header themselves.

The counts are kept in each web worker's memory, so a site with two workers allows
up to ten attempts a minute in total, and a reload resets them. With a long random
password that is still far too slow for guessing to work.
