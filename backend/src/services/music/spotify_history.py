"""Import Spotify Extended Streaming History without extracting private archives.

Run from backend/src:
python -B -m services.music.spotify_history C:/path/to/my_spotify_data.zip
"""
import argparse
import calendar
from collections import Counter
from contextlib import closing
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sqlite3
import zipfile

from services.music.spotify_auth import token_path


def six_months_before(value):
    month_index = value.year * 12 + value.month - 1 - 6
    year, month = divmod(month_index, 12)
    month += 1
    return value.replace(year=year, month=month,
                         day=min(value.day, calendar.monthrange(year, month)[1]))


def timestamp(value):
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError("History timestamp must include a timezone")
    return parsed.astimezone(timezone.utc).isoformat(timespec="microseconds")


def import_history(archive, database, on_import=None):
    """Atomic import. Exact repeats of (track, end timestamp, duration) count once."""
    database = Path(database)
    database.parent.mkdir(parents=True, exist_ok=True)
    stats = Counter()
    with closing(sqlite3.connect(database)) as connection, connection:
        connection.execute("""CREATE TABLE IF NOT EXISTS spotify_history (
            track_id TEXT NOT NULL, ended_at TEXT NOT NULL, ms_played INTEGER NOT NULL,
            PRIMARY KEY (track_id, ended_at, ms_played))""")
        connection.execute("CREATE INDEX IF NOT EXISTS history_ended_at ON spotify_history(ended_at)")
        with zipfile.ZipFile(archive) as zipped:
            entries = [entry for entry in zipped.infolist()
                       if re.fullmatch(r"Streaming_History_(Audio|Video)_.+\.json", Path(entry.filename).name)]
            if not entries:
                raise ValueError("No Extended Streaming History JSON files found in the ZIP.")
            for entry in entries:
                if entry.file_size > 100 * 1024 * 1024:
                    raise ValueError("History file exceeds the 100 MiB import limit.")
                with zipped.open(entry) as stream:
                    records = json.load(stream)
                if not isinstance(records, list):
                    raise ValueError("Expected a list of history records.")
                stats["files"] += 1
                for record in records:
                    stats["records_scanned"] += 1
                    if not isinstance(record, dict):
                        raise ValueError("Invalid history record; import rolled back.")
                    uri = record.get("spotify_track_uri")
                    if not uri:
                        stats["non_track_records"] += 1
                        continue
                    if not isinstance(uri, str) or not re.fullmatch(r"spotify:track:[A-Za-z0-9]{22}", uri):
                        stats["unsupported_track_uris"] += 1
                        continue
                    duration = record.get("ms_played")
                    if type(duration) is not int or duration < 0:
                        raise ValueError("Invalid listening duration; import rolled back.")
                    ended_at = timestamp(record["ts"])
                    cursor = connection.execute("INSERT OR IGNORE INTO spotify_history VALUES (?, ?, ?)",
                                                (uri.rsplit(":", 1)[1], ended_at, duration))
                    stats["inserted" if cursor.rowcount else "duplicate_records"] += 1
        count, first, last = connection.execute(
            "SELECT COUNT(*), MIN(ended_at), MAX(ended_at) FROM spotify_history").fetchone()
        if on_import is not None:
            on_import(connection)
    return {**stats, "stored_records": count, "first_record": first, "last_record": last}


def rank_history(database, as_of, minimum_ms=30000):
    """Rolling six calendar months in UTC, inclusive start and exclusive end.

    This is our catalog's counting rule, not a claim about Spotify's own metrics.
    Zero-duration records never count. End timestamps are as supplied by Spotify.
    """
    if as_of.tzinfo is None or minimum_ms < 1:
        raise ValueError("Use a timezone-aware cutoff and a positive minimum duration.")
    end = as_of.astimezone(timezone.utc)
    start = six_months_before(end)
    with closing(sqlite3.connect(Path(database).resolve().as_uri() + "?mode=ro", uri=True)) as connection:
        rows = connection.execute("""SELECT track_id, COUNT(*) AS plays, SUM(ms_played) AS duration
            FROM spotify_history WHERE ended_at >= ? AND ended_at < ? AND ms_played >= ?
            GROUP BY track_id ORDER BY plays DESC, duration DESC, track_id ASC""",
            (timestamp(start.isoformat()), timestamp(end.isoformat()), minimum_ms)).fetchall()
    return [{"track_id": track, "plays": plays, "ms_played": duration} for track, plays, duration in rows]


def catalog_preview(database, catalog, as_of, minimum_ms):
    rankings = rank_history(database, as_of, minimum_ms)
    with closing(sqlite3.connect(Path(catalog).resolve().as_uri() + "?mode=ro", uri=True)) as connection:
        ids = {row[0] for row in connection.execute("SELECT track_id FROM music_catalog")}
    matched = [row for row in rankings if row["track_id"] in ids]
    return {"window_start": six_months_before(as_of).isoformat(), "window_end": as_of.isoformat(),
            "minimum_listening_ms": minimum_ms, "catalog_tracks": len(ids),
            "distinct_tracks_played": len(rankings), "catalog_tracks_played": len(matched),
            "catalog_tracks_without_qualifying_plays": len(ids) - len(matched),
            "played_tracks_outside_current_catalog": len(rankings) - len(matched),
            "qualifying_plays": sum(row["plays"] for row in rankings)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--minimum-ms", type=int, default=30000)
    args = parser.parse_args()
    if args.minimum_ms < 1:
        parser.error("--minimum-ms must be positive")
    database = token_path().parent / "spotify-history.db"
    summary = import_history(args.archive, database)
    catalog = Path(__file__).resolve().parents[3] / "portfolio.db"
    summary["preview"] = catalog_preview(database, catalog, datetime.now(timezone.utc), args.minimum_ms)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
