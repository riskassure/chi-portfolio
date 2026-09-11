# Spotify connection (local development)

Authorization, token refresh, history import, playlist synchronization and ranked
catalog publication are implemented. The local Windows task can collect activity
every 15 minutes and publish when seven days have elapsed since the last success.

1. Run `python -B app.py` from `backend/src` and serve the frontend on port 5500.
2. In the Spotify developer app, allow this exact redirect:
   `http://127.0.0.1:5000/api/music/spotify/callback`.
3. Open `http://127.0.0.1:5000/api/music/spotify/connect`.
4. If your admin session is missing, the setup page asks for your existing
   portfolio admin password directly on the backend. This avoids cross-origin
   login cookie issues. An existing admin session proceeds without another login.
5. Enter the app's **Client ID**, then approve the requested read permissions on
   Spotify. PKCE requires no Client Secret. The callback shows connection status.

On Windows, tokens are stored in
`%LOCALAPPDATA%/chi-portfolio/spotify-tokens.json`, outside the repository and the
static server's directory. This is a local credential file: do not share it.
On other platforms the fallback is `~/.local/share/chi-portfolio/`.
The directory inherits the Windows user profile's permissions. Tokens are not
encrypted by this implementation. Delete the file and revoke the app in Spotify
account settings to disconnect fully.

Setup routes require a local admin session and the exact loopback host/port above;
they are disabled when `FLASK_ENV=production`. Pending authorizations expire after
10 minutes and are held in process memory; restart/reload requires reconnecting.
No credentials are returned in the connection-status response or stored in Flask
cookies. A saved connection does not prove Spotify has not revoked authorization;
an API operation must validate it. Refresh rejection requires reconnecting.

Validation: `python -B -m unittest discover -s backend/tests -p 'test_spotify_auth.py'`
from the repository root. Tests use temporary files and mocked Spotify responses.
Real account authorization still requires the owner's browser.

## Import listening history

From `backend/src`, run:

```powershell
python -B -m services.music.spotify_history C:/path/to/my_spotify_data.zip --minimum-ms 30000
```

The ZIP is read in place without extracting files. Only Spotify track IDs, UTC
end timestamps, and listening durations are stored in `spotify-history.db` beside
the private token file. IP addresses, devices, locations and other export fields
are not stored. Podcast and other records without track URIs are excluded.
The entire available music history is retained privately for later recalculation.

### Automatic download import

The installed task and **Update now** also check the Windows user's
`~/Downloads` folder (on this laptop, `C:/Users/riska/Downloads`). Request and
download Extended Streaming History yourself; Spotify's export request and
download are not automated. Leave `spotify` in the ZIP filename, for example
`my_spotify_data.zip` or `my_spotify_data (1).zip`. Other ZIPs are ignored.
The existing 15-minute task picks it up while logged in and online, or you can
press **Update now**. Files modified within the last minute or accompanied by
download-in-progress files are deferred to a later check.

SHA-256 fingerprints in the private history database identify previously imported
contents, even when renamed. Recording the fingerprint and marking publication
pending happen in the same transaction as the history import. New archives force
a ranking refresh without waiting a week; failed Spotify requests keep that refresh
pending for retry. The same completed archive does not repeatedly trigger refreshes.
Malformed archives are left untouched and reported to the admin; corrected files
can be retried. Originals are never moved, deleted, or extracted. Archives must be
at most 512 MiB, with individual history JSON files at most 100 MiB.
Exact repeated `(track ID, end timestamp, duration)` tuples count once, including
across imports. Malformed track records roll back the import.

The confirmed counting rule is at least 30 seconds per record. Rankings use the
last six calendar months in UTC, inclusive start and exclusive end, based on the
export's end timestamps. Equal play counts sort by total listening duration then
track ID. This is a site-specific counting rule, not Spotify's affinity ranking.
The command reports a preview against the existing catalog using exact track ID
matches; alternate releases may have different IDs. It does not publish rankings
or modify the catalog. It reports the latest imported timestamp so an older export
is not mistaken for coverage through today.

Run all Spotify tests with:
`python -B -m unittest discover -s backend/tests -p 'test_spotify*.py'`
from the repository root.

## Publish and schedule locally

From `backend/src`, run `python -B -m services.music.spotify_jobs --refresh` for
an immediate playlist sync and ranked publication. Without `--refresh`, each run
collects recent activity and only publishes if the last publication is a week old.
Run `backend/install_music_schedule.ps1` in PowerShell to register the current
user's **Chi Portfolio Spotify Refresh** task. It runs with `pythonw.exe` without
opening a console, at logon and every 15 minutes while the user is logged in.
The laptop must be awake and online. This does not deploy the website or change
power settings. The job runs independently of Flask and the frontend server.
Disable it with `Disable-ScheduledTask -TaskName 'Chi Portfolio Spotify Refresh'`.

After a shutdown, the sign-in trigger checks the persisted last successful
publication immediately. If seven days have elapsed, that run publishes the missed
weekly update; it does not wait for another weekly date. This is a per-user task,
so it runs after Windows sign-in, not on the lock screen before anyone logs in.
`StartWhenAvailable` catches missed scheduled starts, and the task requires a
network connection. Failed runs retry every five minutes up to three times, in
addition to the regular 15-minute schedule. Temporary network/local failures use
a five-minute backoff; Spotify HTTP failures retain the longer one-hour minimum
and any longer Retry-After. No update can succeed while Spotify is unreachable or
reauthorization is required.

The music page's admin controls include **Update now**. It performs a full playlist
and ranking refresh even if the weekly update is not due, using an authenticated,
CSRF-protected POST to `/api/music/spotify/refresh`. The button shows progress and
reloads the displayed catalog after success. A concurrent update or a Spotify
retry window is reported without launching duplicate work or bypassing throttling.
The manual and scheduled paths share the same cross-process SQLite lock. Manual
updates require the local backend to be running; scheduled updates do not.

The scheduler code checks the seven-day interval itself, so a missed weekly run
can be performed by the next successful run. A separate SQLite lock prevents
overlapping jobs. Spotify HTTP failures back off for at least an hour (respecting a
longer Retry-After) and retain the previous publication. Completed playlists are
cached by snapshot ID privately; failed partial playlist reads are never cached.
Current playlists returning 403/404 are excluded and the publication reports how
many could not be accessed. Transient or rate-limit failures abort publication.

`music_publication` and `music_publication_meta` in the catalog database hold the
published snapshot. The original catalog is preserved. Its row count at first
publication becomes the persistent target N (2,461 for this site); eligible songs
are unique Spotify track IDs across accessible current playlists. Ranking uses
verified six-month play counts, then duration, then track ID. Zero-count tracks
fill remaining slots. Spotify-provided relinking IDs can match older history;
we do not infer alternate-recording matches from titles. Source playlist membership
is preserved for every candidate. Existing curated metadata and later admin edits
are retained; composer fields for new API tracks remain blank rather than guessing.

The music API filters and sorts the published list before pagination. The site
shows 25 records per page, rank, play count, publication date, window and the latest
export timestamp. Search/filtering stays within the top N published list.
Only aggregate counts and catalog metadata are published; raw history and tokens
remain private. `/api/music/spotify/status` is accessible only to the local admin.

**Duration limitation:** recently-played API events have no listening duration and
their timestamps are not interchangeable with export end timestamps. They are
stored separately in `recent_activity`, deduplicated by track ID and played_at,
and NEVER added to duration-verified counts. Future exports are still required to
verify new 30-second plays; downloaded ZIPs are now imported automatically. Automatic publication refreshes membership and the
rolling window, but cannot invent missing listening durations. The API also cannot
guarantee complete collection after sleep/offline gaps. The public history-through
date makes the export cutoff visible.

References:
- https://developer.spotify.com/documentation/web-api/tutorials/code-pkce-flow
- https://developer.spotify.com/documentation/web-api/tutorials/refreshing-tokens
