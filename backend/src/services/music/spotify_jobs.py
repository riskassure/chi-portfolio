"""Run local collection every 15 minutes and publish a complete catalog weekly."""
import argparse
from contextlib import closing
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import time

from services.music.music_catalog import publish
from services.music.spotify_api import SpotifyApi, SpotifyApiError
from services.music.spotify_auth import SpotifyError, token_path
from services.music.spotify_sync import collect_recent, connect, sync_playlists


def run_job(catalog, history, api, now=None, force=False):
    now = now or datetime.now(timezone.utc)
    with closing(connect(history)) as db:
        state = dict(db.execute("SELECT key, value FROM sync_state"))
    if float(state.get("retry_after", 0)) > now.timestamp():
        return {"status": "waiting", "message": "Waiting before retrying Spotify."}
    report = {"status": "ok", "checked_at": now.isoformat()}
    try:
        report["recent_records_added"] = collect_recent(api, history)
        last = float(state.get("last_publication", 0))
        if force or now.timestamp() - last >= 7 * 86400:
            candidates, summary = sync_playlists(api, history)
            report["publication"] = publish(catalog, history, candidates, summary, now)
            state["last_publication"] = str(now.timestamp())
        state["retry_after"] = "0"
    except (SpotifyError, sqlite3.Error, ValueError, KeyError, OSError, TypeError) as exc:
        report["status"] = "error"
        # Do not store arbitrary exception strings: they may contain request data.
        report["message"] = str(exc) if isinstance(exc, SpotifyError) else "Local refresh failed; the previous catalog is retained."
        delay = max(3600, exc.retry_after) if isinstance(exc, SpotifyApiError) else 3600
        state["retry_after"] = str(now.timestamp() + delay)
    state["job_status"] = json.dumps(report)
    with closing(connect(history)) as db, db:
        db.executemany("INSERT OR REPLACE INTO sync_state VALUES (?, ?)", state.items())
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="Refresh the publication even if a week has not elapsed")
    args = parser.parse_args()
    private = token_path().parent
    private.mkdir(parents=True, exist_ok=True)
    # Separate lock database prevents overlapping task instances without holding
    # a transaction on the listening-history database across network requests.
    with closing(sqlite3.connect(private / "spotify-job-lock.db", timeout=1)) as lock:
        try:
            lock.execute("BEGIN IMMEDIATE")
        except sqlite3.OperationalError:
            return
        history = private / "spotify-history.db"
        catalog = Path(__file__).resolve().parents[3] / "portfolio.db"
        report = run_job(catalog, history, SpotifyApi(), force=args.refresh)
        if __import__("sys").stdout is not None:
            print(json.dumps(report, indent=2))
        if report["status"] == "error":
            raise SystemExit(1)


if __name__ == "__main__":
    main()
