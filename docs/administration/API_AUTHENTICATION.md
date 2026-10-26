# How the site's logins and API keys work

A plain-language guide to every credential the website and its helper use: what
each one is for, how it was obtained, where it lives, how it renews, and what to
check when access fails. It assumes no background in web authentication. Checked
against the code on 2026-10-26 (`backend/src/app.py`, `start_local.py`,
`local_admin_password.py`, `pythonanywhere_wsgi.py`, `pythonanywhere_api.py`,
`site_deployment.py`, the SSH callers in `backend/`, `services/music/spotify_auth.py`,
`routes/music_spotify.py`, `services/photography/google_photos_auth.py`,
`routes/google_photos.py`, `routes/travel.py`).

The table of file locations is in the runbook's
[Credentials and renewals](../ADMIN_RUNBOOK.md#credentials-and-renewals). Never put
a credential's value in documentation, git, a screenshot or a command line.

## Three ideas that cover almost everything

**1. Proving who you are vs. being allowed to do something.** *Authentication* is
proving identity (a password, a key). *Authorization* is what that identity may do
(read your top tracks, but not change playlists). Most credentials here do both: a
token both identifies the program and carries a list of what it may do, called its
**scope**.

**2. Secrets that travel with each request.** A web server doesn't remember you
between requests. So after you prove who you are once, the program keeps a token
and sends it with every later request, in a request header such as
`Authorization: Token ...` or as a browser cookie. Anyone who copies the token can
act as you until it expires or is revoked, which is why the files that hold them
stay private and outside the repository.

**3. Short-lived access, long-lived renewal.** OAuth services (Spotify, Google) hand
out two tokens: an **access token** that works for about an hour, and a **refresh
token** that lasts much longer and is used only to get a new access token. The
program renews quietly in the background. You only go through the browser approval
again if the refresh token is refused (revoked, expired, or replaced).

## At a glance

| Credential | Used for | How you got it | Where it lives | Renewal | When it fails |
| --- | --- | --- | --- | --- | --- |
| Website admin password (live) | Signing in on `www.cwoo.me` to edit | Chosen at hosting setup | Server: `hosting.json` | Manual, when you decide | 401 "Invalid credentials" |
| Website admin password (local) | Signing in on `127.0.0.1:5001` | Chosen on first local start | Laptop: `local-admin-password.dpapi` (encrypted for your Windows account) | `start_local.py --reset-password` | "Cannot read saved local password" |
| Session cookie | Staying signed in after login | Given by Flask at login | Your browser | Lasts 8 hours; sign in again | 403 on edit buttons |
| PythonAnywhere API token | Helper uploads packages and reloads the site | PythonAnywhere Account page, API token tab | Laptop: `pythonanywhere-api.json` | Regenerate there, run setup again | "Authentication failed. Check or regenerate your API token." |
| SSH key | Helper runs checks and publishes on the server; option 8 downloads | Created on the laptop; public half added to PythonAnywhere | Laptop: under `%USERPROFILE%\.config`; server: `~/.ssh/authorized_keys` | Doesn't expire | "Permission denied (publickey...)" or a password prompt |
| Spotify tokens | Reading your top tracks for the music page | Browser approval (OAuth with PKCE), on the laptop | Laptop and server: `spotify-tokens.json` | Automatic refresh | "Spotify rejected the authorization. Please connect again." |
| Google Photos app credentials | Identifying this app to Google | Downloaded from Google Cloud Console | Laptop: `google-oauth.json` | Only if you change the app | "Check the private google-oauth.json file..." |
| Google Photos tokens | Letting the local import screen read photos you pick | Browser approval (OAuth with PKCE), on the laptop | Laptop: `google-photos-tokens.json` | Automatic refresh | Connect again |
| Esri map key | Drawing the travel map's base map | ArcGIS developer dashboard | `esri-api-key.txt` on laptop and server | Expires **2027-10-13**; replace before then | Map area shows an error; `/api/travel/config` returns 503 |

The sections below explain each one.

## The website's own admin login

**What happens.** On `admin_dashboard.html` you type the admin password. The page
sends it to `/api/login`. Flask compares it with the configured password (a
constant-time comparison, so timing doesn't leak it). If it matches, Flask gives
your browser a **session cookie**: a small piece of data saying "is_admin", with a
signature made from a server-side secret (`FLASK_SECRET_KEY`). The browser sends
the cookie back with every request; admin routes refuse requests without a valid
one (HTTP 403). The cookie can't be forged without the secret, and JavaScript on
the page can't read it.

**Live vs. local.**

- Live: the password and secret come from `/home/cwoo/.config/chi-portfolio/hosting.json`,
  which `pythonanywhere_wsgi.py` reads at start-up. Production refuses to start
  with a password under 16 characters or a secret under 32.
- Local: `start_local.py` (option 6) decrypts your saved local password and makes a
  **new random secret each time it starts**. That's why restarting option 6 signs
  you out.

**Protections.** Five login attempts per minute per address (then HTTP 429). Edits
must come from the site's own address (the request's `Origin` header is checked);
locally, use exactly `http://127.0.0.1:5001`. Sessions last 8 hours.

**When it fails.**

- "Invalid credentials": wrong password for *this* site (local and live differ).
- Edit buttons give 403 or "Unauthorized": the session expired or the local server
  restarted. Sign in again.
- "Request origin rejected": you opened the local site as `localhost:5001` or another
  address. Use `127.0.0.1:5001`.

**Changing the live password.** Edit `ADMIN_PASSWORD` in `hosting.json` on the server,
then reload the web app from the Web tab. Changing `FLASK_SECRET_KEY` as well signs
everyone out.

## PythonAnywhere: API token and SSH

The helper reaches the server in two ways, each with its own credential.

**API token** (a long random string, sent as `Authorization: Token ...`). PythonAnywhere's
web API accepts it in place of your password. The helper uses it to upload packages
(option 3), inspect them, and reload the web app after a code publish (options 15, 16).
You created it on PythonAnywhere's Account page and saved it with
`python backend/pythonanywhere_api.py setup`, which checks it before saving to
`%USERPROFILE%\.config\chi-portfolio\pythonanywhere-api.json`. The file is plain text,
so keep it private. `python backend/pythonanywhere_api.py check` tests it without
changing anything. If it stops working, regenerate the token on the Account page
(the old one stops working), move the old settings file aside, and run `setup` again.

**SSH** (secure shell: a way to run commands on the server over an encrypted
connection). The helper runs `ssh cwoo@ssh.pythonanywhere.com ...` for live checks
(option 4), publishing (option 5), option 8 downloads, batch and merge checks, and
the Esri key upload (option 17). SSH can log in with your PythonAnywhere password,
but you use a **key pair** instead:

- The *private key* stays on the laptop, under `%USERPROFILE%\.config`
  (`C:\Users\riska\.config`), protected by a passphrase you type when it is used.
  That isn't OpenSSH's default folder (`%USERPROFILE%\.ssh\`), so the laptop's SSH
  setup has to point to it, for example with an `IdentityFile` line in
  `%USERPROFILE%\.ssh\config` or by loading it into the ssh-agent. If the key
  ever seems to be ignored, check that pointer first.
- The *public key* was added to `/home/cwoo/.ssh/authorized_keys` on the server.
  It's fine for anyone to see; it can only check signatures, not make them.

At each connection the server sends a challenge, the laptop signs it with the
private key, and the server checks the signature with the public key. The key
never leaves the laptop and doesn't expire. The first time, SSH also records the
server's own key in `known_hosts`, and warns loudly if it ever changes.

When SSH fails: "Permission denied (publickey)" means the server doesn't have your
public key or the laptop can't find the private one (see the folder note above). A password prompt means the
key wasn't used; your PythonAnywhere password works, but check why. A "REMOTE HOST
IDENTIFICATION HAS CHANGED" warning means stop and check with PythonAnywhere before
continuing.

## OAuth, in plain terms (Spotify and Google Photos)

OAuth lets this program read some of your data at Spotify or Google **without ever
seeing your Spotify or Google password**. You sign in at their site, they ask you to
approve a specific permission, and they hand the program a token limited to that
permission. Both integrations here use the **authorization-code flow with PKCE**:

1. **The program asks.** You click Connect on the local server. The program makes a
   random secret (the *code verifier*), keeps it in memory, and sends your browser to
   Spotify or Google with: its app ID (*client ID*), the permission it wants
   (*scope*), where to send you back (*redirect URI*), a random *state* value, and a
   hash of the verifier (the *code challenge*).
2. **You approve.** At Spotify or Google you sign in (if needed) and see what the
   app is asking for. You click Allow.
3. **They send you back with a one-time code.** Your browser returns to the redirect
   URI on `127.0.0.1:5001` with a short-lived *authorization code* and the same
   *state*. The program checks the state matches what it sent from this browser, so
   a forged return link is refused.
4. **The program swaps the code for tokens.** It sends the code plus the original
   verifier directly to Spotify or Google. They check the verifier against the hash
   from step 1. That is PKCE: even someone who intercepted the code can't use it
   without the verifier. They reply with an access token, a refresh token and how
   long the access token lasts.
5. **The program saves the tokens** in a private file outside the repository and uses
   the access token for API calls, refreshing it when it is within a minute of
   expiring.

Pending approvals expire after 10 minutes and are held in memory only, so finish
the approval in the same browser without restarting the local server.

The redirect URI must match, character for character, the one registered with
Spotify or Google, which is why the connection only works at `http://127.0.0.1:5001`.
These setup pages refuse to run on the live site.

### Spotify

- **What it requests:** the scope `user-top-read`, your top tracks only. It can't
  change your account or playlists.
- **App identity:** your Spotify developer app's client ID, typed into the connect
  form. With PKCE, Spotify needs no client secret, so none is stored.
- **Redirect URI** registered in the Spotify developer dashboard:
  `http://127.0.0.1:5001/api/music/spotify/callback`.
- **Connect:** option 6, then `http://127.0.0.1:5001/api/music/spotify/connect`. It asks
  for the local admin password first. Details in [Spotify](../features/music/SPOTIFY.md).
- **Tokens:** `%LOCALAPPDATA%\chi-portfolio\spotify-tokens.json` on the laptop. The live
  site's daily refresh uses its own copy at
  `/home/cwoo/.config/chi-portfolio/spotify-tokens.json`, transferred privately.
- **Renewal:** automatic. Each refresh can return a new refresh token, which the
  program saves. That is why only one place should refresh with a given set of tokens:
  if the laptop and the server both refreshed from the same copy, one could replace
  the refresh token and leave the other with a refused one. This is the reason the
  old laptop job stays disabled.
- **When it fails:** the music page keeps the last good list. "Spotify rejected the
  authorization. Please connect again." means the refresh token was refused (revoked in
  your Spotify account settings, or replaced). Reconnecting on the laptop updates only
  the laptop's file. Getting a fresh set to the server is the private transfer the
  runbook mentions; that procedure will be written up after a real run.
- **Disconnect fully:** delete the token file and remove the app's access in your Spotify
  account settings (Manage apps).

### Google Photos

- **What it requests:** the scope `photospicker.mediaitems.readonly`, read access only
  to photos you choose in Google's picker, not your whole library.
- **App identity:** a Google Cloud "OAuth web client", downloaded as
  `%USERPROFILE%\.config\chi-portfolio\google-oauth.json`. Unlike Spotify, Google's web
  clients also send a **client secret** when swapping or refreshing tokens, so this file
  is a credential too. The program checks that it lists the exact redirect URI.
- **Redirect URI** registered in Google Cloud: `http://127.0.0.1:5001/auth/google/callback`.
- **Connect:** option 6, then `http://127.0.0.1:5001/api/photography/google/connect`
  (or Connect Google Photos on the local photography page). Use the Google account
  registered as a test user. Details in [Google Photos](../features/photography/GOOGLE_PHOTOS.md).
- **Tokens:** `%LOCALAPPDATA%\chi-portfolio\google-photos-tokens.json`, laptop only. The
  live site never talks to Google Photos; imported photos are published with options 11-13.
- **Renewal:** automatic refresh. The program asks for offline access so Google issues a
  refresh token. While the Google Cloud app is in *Testing* status, Google limits how
  long that authorization lasts (Google documents seven days), so expect to connect
  again before an import after a gap.
- **When it fails:** connect again. If the error names `google-oauth.json`, the file is
  missing, unreadable, or doesn't list the redirect URI above; download it again from
  Google Cloud after checking the URI.

## Esri map key (a public key, on purpose)

The travel map draws its base map from Esri. Esri needs a key, and the visitor's
**browser** fetches the map tiles, so the key has to be in the browser. The page gets
it from `/api/travel/config`, which reads `esri-api-key.txt` from the server account's
home folder (or the `ESRI_BASEMAP_API_KEY` environment variable). Anyone can see it.

It's safe because of two limits set in the ArcGIS dashboard: it is allowed only map
basemap access, and only for requests whose **referrer** (the page address the browser
reports when it asks Esri for tiles) is this site, plus the local addresses. Someone
copying the key onto their own site would be refused. Keep those limits, and never put
a more powerful ArcGIS credential in that file.

- **Renewal:** it expires on **2027-10-13**. Create a new key with the same limits, save it
  to the laptop file, and upload it with option 17. Changing referrers can mean
  generating a new key.
- **When it fails:** `/api/travel/config` returns 503 when the file is missing or empty.
  If the map loads but tiles fail, check F12 Network for Esri requests refused with
  401 or 403 (wrong referrer, expired key).

## Where to look when access fails

| Message or symptom | Credential | First check |
| --- | --- | --- |
| "Invalid credentials" at sign-in | Admin password | Local and live passwords differ |
| 403 on edit actions, "Unauthorized access rejected" | Session cookie | Sign in again; local restarts sign you out |
| "Request origin rejected" | Origin check | Use `http://127.0.0.1:5001` exactly, or the `https://www.cwoo.me` address |
| "Too many login attempts" | Login limit | Wait a minute |
| "Authentication failed. Check or regenerate your API token." | PythonAnywhere API token | `python backend/pythonanywhere_api.py check` |
| "Permission denied (publickey)" or an unexpected password prompt | SSH key | Is the key loaded and the public half in `authorized_keys`? |
| "Spotify rejected the authorization. Please connect again." | Spotify refresh token | Reconnect on the laptop; check the server copy separately |
| "Authorization expired or did not match this browser" | Pending OAuth approval | Start the connection again, same browser, within 10 minutes |
| "Check the private google-oauth.json file..." | Google app credentials | File present and lists the exact redirect URI |
| "Map basemap access is not configured." | Esri key | Key file present on that machine (option 17 uploads it) |
