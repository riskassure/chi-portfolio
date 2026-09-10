"""Cache complete playlists and collect duration-unverified recent activity privately."""
from contextlib import closing
from datetime import datetime, timezone
import json
import re
import sqlite3
import time

from services.music.spotify_api import SpotifyApiError
from services.music.spotify_auth import SpotifyError
from services.music.spotify_history import timestamp

TRACK_ID = re.compile(r"[A-Za-z0-9]{22}")


def connect(database):
    connection = sqlite3.connect(database, timeout=30)
    connection.execute("""CREATE TABLE IF NOT EXISTS playlist_cache (
        playlist_id TEXT PRIMARY KEY, snapshot TEXT, payload TEXT NOT NULL)""")
    connection.execute("""CREATE TABLE IF NOT EXISTS recent_activity (
        track_id TEXT, played_at TEXT, PRIMARY KEY(track_id, played_at))""")
    connection.execute("CREATE TABLE IF NOT EXISTS sync_state (key TEXT PRIMARY KEY, value TEXT)")
    connection.commit()
    return connection


def sync_playlists(api, database, progress=lambda message: None):
    playlists = list(api.items("/me/playlists?limit=50"))
    tracks = {}
    skipped = []
    with closing(connect(database)) as db:
        for index, playlist in enumerate(playlists):
            playlist_id = playlist["id"]
            if not TRACK_ID.fullmatch(playlist_id):
                raise SpotifyError("Invalid playlist identifier.")
            snapshot = playlist.get("snapshot_id")
            cached = db.execute("SELECT snapshot, payload FROM playlist_cache WHERE playlist_id=?", (playlist_id,)).fetchone()
            if cached and snapshot and cached[0] == snapshot:
                items = json.loads(cached[1])
            else:
                try:
                    items = list(api.items(f"/playlists/{playlist_id}/items?limit=50"))
                    # Do not label a partially changed playlist as a complete cached snapshot.
                    if snapshot and api.get(f"/playlists/{playlist_id}").get("snapshot_id") != snapshot:
                        raise SpotifyError("A playlist changed during refresh. Please retry.")
                except SpotifyApiError as exc:
                    if exc.status not in (403, 404):
                        raise
                    skipped.append(playlist_id)
                    continue
                with db:
                    db.execute("INSERT OR REPLACE INTO playlist_cache VALUES (?, ?, ?)",
                               (playlist_id, snapshot, json.dumps(items)))
            name = playlist.get("name", "Untitled playlist").strip()
            for entry in items:
                track = entry.get("item", entry.get("track"))
                if not track or track.get("type") != "track" or track.get("is_local"):
                    continue
                track_id = track.get("id", "")
                if not TRACK_ID.fullmatch(track_id or ""):
                    continue
                row = tracks.setdefault(track_id, {"track": track, "playlists": set(), "aliases": {track_id}})
                row["playlists"].add(name)
                original_id = (track.get("linked_from") or {}).get("id")
                if original_id and TRACK_ID.fullmatch(original_id):
                    row["aliases"].add(original_id)
            progress(f"Playlists checked: {index + 1}/{len(playlists)}; unique tracks: {len(tracks)}")
    if not tracks:
        raise SpotifyError("No accessible playlist tracks; the previous catalog is retained.")
    return tracks, {"playlist_count": len(playlists), "inaccessible_playlists": len(skipped)}


def collect_recent(api, database):
    # Store API events separately: played_at is not the export's end timestamp,
    # and the API provides no listening duration with which to enforce 30 seconds.
    with closing(connect(database)) as db:
        latest = db.execute("SELECT MAX(played_at) FROM recent_activity").fetchone()[0]
        url = "/me/player/recently-played?limit=50"
        if latest:
            url += "&after=" + str(int(datetime.fromisoformat(latest).timestamp() * 1000) - 1)
        records = list(api.items(url))
        added = 0
        with db:
            for item in records:
                track_id = (item.get("track") or {}).get("id", "")
                if not TRACK_ID.fullmatch(track_id or ""):
                    continue
                added += db.execute("INSERT OR IGNORE INTO recent_activity VALUES (?, ?)",
                                    (track_id, timestamp(item["played_at"]))).rowcount
            db.execute("INSERT OR REPLACE INTO sync_state VALUES ('last_collection', ?)", (str(time.time()),))
    return added
