"""Publish and query an atomic ranked catalog, preserving curated source rows."""
from contextlib import closing
import json
import math
from pathlib import Path
import sqlite3

from services.music.spotify_history import rank_history, six_months_before

EDITABLE = ("genre", "composition_name", "track_name", "composer", "performer")
SORTABLE = set(EDITABLE) | {"rank", "plays", "spotify_playlist", "album_name", "release_date", "duration_string", "popularity"}


def tables(db):
    db.execute("CREATE TABLE IF NOT EXISTS music_publication (track_id TEXT PRIMARY KEY, rank INTEGER, data TEXT NOT NULL)")
    db.execute("CREATE TABLE IF NOT EXISTS music_publication_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    db.execute("CREATE TABLE IF NOT EXISTS music_overrides (track_id TEXT, field TEXT, value TEXT, PRIMARY KEY(track_id, field))")


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


def read_catalog(catalog, page=1, per_page=25, search="", playlist="all", sorts=None):
    with closing(sqlite3.connect(Path(catalog).resolve().as_uri() + "?mode=ro", uri=True)) as db:
        db.row_factory = sqlite3.Row
        published = db.execute("SELECT 1 FROM sqlite_master WHERE name='music_publication_meta'").fetchone()
        meta = {r["key"]: json.loads(r["value"]) for r in db.execute("SELECT * FROM music_publication_meta")} if published else {}
        if meta:
            rows = [json.loads(r[0]) for r in db.execute("SELECT data FROM music_publication ORDER BY rank")]
            by_id = {r["track_id"]: r for r in rows}
            for override in db.execute("SELECT * FROM music_overrides"):
                if override["track_id"] in by_id:
                    by_id[override["track_id"]][override["field"]] = override["value"]
        else:
            rows = [dict(r) for r in db.execute("SELECT * FROM music_catalog ORDER BY id")]
            for row in rows:
                row["playlists"] = [row["spotify_playlist"]] if row.get("spotify_playlist") else []
        playlists = sorted({name for row in rows for name in row["playlists"]})
        query = search.casefold().strip()
        rows = [r for r in rows if (playlist == "all" or playlist in r["playlists"]) and
                (not query or any(query in str(v).casefold() for v in r.values() if v is not None))]
        for rule in reversed((sorts or [])[:10]):
            field = rule.get("column")
            if not isinstance(field, str) or field not in SORTABLE or rule.get("direction") not in ("asc", "desc"):
                continue
            numeric = field in ("rank", "plays", "popularity")
            rows.sort(key=lambda r: (r.get(field) or 0) if numeric else str(r.get(field) or "").casefold(),
                      reverse=rule["direction"] == "desc")
        total = len(rows)
        pages = max(1, math.ceil(total / per_page))
        page = min(max(1, page), pages)
        return {"data": rows[(page - 1) * per_page:page * per_page], "page": page, "per_page": per_page,
                "total_pages": pages, "total_records": total, "playlists": playlists, "ranking": meta or None}
