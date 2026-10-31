# Renewing the Spotify sign-in

Written 2026-10-30 from a real renewal (see [What was tested](#what-was-tested)).

## When you need this

The live music page is refreshed once a day by a PythonAnywhere task that reads your
Spotify top tracks with a saved sign-in, a *token* file on the server:
`/home/cwoo/.config/chi-portfolio/spotify-tokens.json`. Each refresh can swap the
token for a new one, so normally it renews itself forever. You need this page when:

- the Spotify task's log (Tasks tab, log button) says
  `Spotify rejected the authorization. Please connect again.`, or
- the live music page's **Updated** date stops moving, or
- you removed the app's access in your Spotify account, or
- you rebuilt the site on a new account ([recovery guide](backups/SITE_DOWN_RECOVERY.md#d-rebuild-on-a-new-account)).

When it fails, the music page keeps showing the last good list. Nothing breaks for
visitors; it just stops updating.

## Why it works this way

Spotify only lets you sign in from the laptop, at `http://127.0.0.1:5001`, because
that's the address registered with your Spotify app. So you sign in on the laptop,
which writes a fresh token file there, then copy that file to the server.

Afterwards the laptop's copy must be deleted. A token can be used by one place only:
if the laptop and the server both refreshed from the same copy, one would get a new
token and the other's copy would be refused.

## Steps (about 10 minutes)

Each block says which window it goes in. **PA console** = pythonanywhere.com, Consoles,
Bash. **Laptop PowerShell** = PowerShell in `C:\Development\chi-portfolio`.

### 1. Keep a copy of the current server token (PA console)

```bash
cd ~/.config/chi-portfolio && cp -p spotify-tokens.json spotify-tokens.before-renewal-$(date -u +%Y%m%d).json && ls -la
```

(On a freshly rebuilt account there's no token yet; skip this step.)

### 2. Sign in on the laptop (browser)

1. Helper, option **6** (local server). Leave it running.
2. Open `http://127.0.0.1:5001/api/music/spotify/connect`. Enter the local admin
   password if asked, then your Spotify app's **Client ID**, and approve on Spotify's
   page. Finish within 10 minutes.
3. The page shows `"connected": true` and "Connection saved. Return to the music page
   and click Update now…". **Don't press Update now** for a renewal: the laptop must not
   use this token itself.
4. Stop the local server (Ctrl+C).

The token is now in `%LOCALAPPDATA%\chi-portfolio\spotify-tokens.json`.

### 3. Copy it to the server (Laptop PowerShell)

```powershell
scp "$env:LOCALAPPDATA\chi-portfolio\spotify-tokens.json" cwoo@ssh.pythonanywhere.com:.config/chi-portfolio/spotify-tokens.json
```

It prints one line with `100%` and the size (about 500 bytes).

### 4. Lock it down and try it (PA console)

```bash
chmod 600 ~/.config/chi-portfolio/spotify-tokens.json
cd ~/chi-portfolio/backend/src && SPOTIFY_TOKEN_PATH=/home/cwoo/.config/chi-portfolio/spotify-tokens.json ~/.virtualenvs/chi-portfolio/bin/python -m services.music.spotify_top --database /home/cwoo/chi-portfolio/backend/portfolio.db --refresh
```

Expect `"status": "ok"` and `"message": "Updated 50 Spotify-ranked tracks."`. Open the
live music page: its Updated time is now.

If it answers `"status": "waiting"` with a `retry_at` time, an earlier failed run set a
retry delay; run it again after that time. If it fails, put the old token back:
`cp -p ~/.config/chi-portfolio/spotify-tokens.before-renewal-*.json ~/.config/chi-portfolio/spotify-tokens.json`.

### 5. Delete the laptop's copy (Laptop PowerShell)

```powershell
Remove-Item "$env:LOCALAPPDATA\chi-portfolio\spotify-tokens.json"
```

The laptop's local music page then says Spotify isn't connected. That's expected.

### 6. Next day

Check the Spotify task's log shows the 16:30 UTC run with `"status": "ok"`. Then
delete the `spotify-tokens.before-renewal-…json` copy on the server (Files tab); it's a
credential you no longer need.

## What was tested

2026-10-30, by Chi, on the live site, while the old token still worked:

- Step 1: backup made (615 bytes, owner-only).
- Step 2: laptop connect returned `"connected": true` at 23:28 UTC.
- Step 3: `scp` copied 523 bytes.
- Step 4: refresh at 23:33:58 UTC: `"status": "ok"`, 50 tracks published, live page
  updated.
- Step 5: laptop copy deleted.

The first attempt at step 4 was pasted into laptop PowerShell, which refused it
harmlessly (`'&&' is not a valid statement separator`); hence the window labels.

Not tested: renewal after Spotify has actually refused a token. The steps are the
same; only step 1's backup would hold a dead token.
