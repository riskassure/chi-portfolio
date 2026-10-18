"""Publish the older export-history ranking; current top tracks use spotify_top.

Writes derived publication tables, preserving source catalog rows and overrides.
Retained for historical tools; importing the shared catalog does not load this module.
"""
from contextlib import closing
import json
import sqlite3

from services.music.music_catalog import tables
from services.music.spotify_history import rank_history, six_months_before


def publish(catalog, history, candidates, playlist_summary, as_of):
    scores = {row["track_id"]: row for row in rank_history(history, as_of)}
    with closing(sqlite3.connect(history)) as db:
        history_latest = db.execute("SELECT MAX(ended_at) FROM spotify_history").fetchone()[0]
    with closing(sqlite3.connect(catalog, timeout=30)) as db, db:
        db.row_factory = sqlite3.Row
        originals = {row["track_id"]: dict(row) for row in db.execute("SELECT * FROM music_catalog")}
        tables(db)
        saved = db.execute("SELECT value FROM music_publication_meta WHERE key='target_count'").fetchone()
        target = int(saved[0]) if saved else len(originals)
        if target < 1:
            raise ValueError("The original catalog must contain tracks before publishing.")
        rows = []
        for track_id, candidate in candidates.items():
            track = candidate["track"]
            artists = [a["name"] for a in track.get("artists", [])]
            album = track.get("album") or {}
            seconds = int(track.get("duration_ms", 0)) // 1000
            row = {"track_id": track_id, "genre": None, "composition_name": None, "unit_name": None,
                   "track_name": track.get("name", ""), "composer": None, "performer": "; ".join(artists),
                   "album_name": album.get("name", ""), "release_date": album.get("release_date", ""),
                   "duration_string": f"{seconds // 60:02}:{seconds % 60:02}", "popularity": None}
            if track_id in originals:
                row.update({k: v for k, v in originals[track_id].items() if k not in ("id", "track_order")})
            row["playlists"] = sorted(candidate["playlists"])
            row["spotify_playlist"] = "; ".join(row["playlists"])
            aliases = {alias for alias in candidate["aliases"] if alias == track_id or alias not in candidates}
            row["plays"] = sum(scores.get(alias, {}).get("plays", 0) for alias in aliases)
            duration = sum(scores.get(alias, {}).get("ms_played", 0) for alias in aliases)
            rows.append((row, duration))
        rows.sort(key=lambda pair: (-pair[0]["plays"], -pair[1], pair[0]["track_id"]))
        selected = [row for row, _ in rows[:target]]
        meta = {"target_count": target, "published_at": as_of.isoformat(),
                "window_start": six_months_before(as_of).isoformat(), "window_end": as_of.isoformat(),
                "history_latest": history_latest, "minimum_ms": 30000,
                "eligible_tracks": len(rows), "tracks_with_plays": sum(row["plays"] > 0 for row in selected),
                **playlist_summary}
        db.execute("DELETE FROM music_publication")
        for rank, row in enumerate(selected, 1):
            row["rank"] = rank
            db.execute("INSERT INTO music_publication VALUES (?, ?, ?)", (row["track_id"], rank, json.dumps(row)))
        for key, value in meta.items():
            db.execute("INSERT OR REPLACE INTO music_publication_meta VALUES (?, ?)", (key, json.dumps(value)))
    return meta
