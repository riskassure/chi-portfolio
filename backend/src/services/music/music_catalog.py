"""Shared catalog schema and queries, plus a lazy legacy publication entry point."""
from contextlib import closing
import json
import math
from pathlib import Path
import sqlite3

EDITABLE = ("genre", "composition_name", "track_name", "composer", "performer")
SORTABLE = set(EDITABLE) | {"rank", "plays", "spotify_playlist", "album_name", "release_date", "duration_string", "popularity"}


def tables(db):
    db.execute("CREATE TABLE IF NOT EXISTS music_publication (track_id TEXT PRIMARY KEY, rank INTEGER, data TEXT NOT NULL)")
    db.execute("CREATE TABLE IF NOT EXISTS music_publication_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    db.execute("CREATE TABLE IF NOT EXISTS music_overrides (track_id TEXT, field TEXT, value TEXT, PRIMARY KEY(track_id, field))")


def publish(catalog, history, candidates, playlist_summary, as_of):
    """Compatibility entry point for the older export-history publisher."""
    # Load history code only when an older caller explicitly publishes that ranking.
    from services.music.history_publication import publish as publish_history
    return publish_history(catalog, history, candidates, playlist_summary, as_of)


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
