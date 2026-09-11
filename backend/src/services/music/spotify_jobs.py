"""Run local collection every 15 minutes and publish a complete catalog weekly."""
import argparse
from contextlib import closing
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3

from services.music.music_catalog import publish
from services.music.spotify_api import SpotifyApi, SpotifyApiError
from services.music.spotify_auth import SpotifyError, token_path
from services.music.spotify_sync import collect_recent, connect, sync_playlists
from services.music.spotify_downloads import import_downloads


def run_job(catalog, history, api, now=None, force=False, downloads=None):
    now = now or datetime.now(timezone.utc)
    archive_report = import_downloads(downloads, history, now.timestamp()) if downloads is not None else None
    with closing(connect(history)) as db:
        state = dict(db.execute("SELECT key, value FROM sync_state"))
    if float(state.get("retry_after", 0)) > now.timestamp():
        return {"status": "waiting", "message": "Waiting before retrying Spotify.",
                "retry_at": datetime.fromtimestamp(float(state["retry_after"]), timezone.utc).isoformat()}
    report = {"status": "ok", "checked_at": now.isoformat(), "archive_import": archive_report}
    try:
        report["recent_records_added"] = collect_recent(api, history)
        last = float(state.get("last_publication", 0))
        if force or state.get("history_publication_pending") == '1' or now.timestamp() - last >= 7 * 86400:
            candidates, summary = sync_playlists(api, history)
            report["publication"] = publish(catalog, history, candidates, summary, now)
            state["last_publication"] = str(now.timestamp())
            state["history_publication_pending"] = '0'
        state["retry_after"] = "0"
    except (SpotifyError, sqlite3.Error, ValueError, KeyError, OSError, TypeError) as exc:
        report["status"] = "error"
        # Do not store arbitrary exception strings: they may contain request data.
        report["message"] = str(exc) if isinstance(exc, SpotifyError) else "Local refresh failed; the previous catalog is retained."
        delay = max(3600, exc.retry_after) if isinstance(exc, SpotifyApiError) else 300
        state["retry_after"] = str(now.timestamp() + delay)
    state["job_status"] = json.dumps(report)
    with closing(connect(history)) as db, db:
        db.executemany("INSERT OR REPLACE INTO sync_state VALUES (?, ?)", state.items())
    return report


def run_local_job(force=False):
    """Shared entry point for the Windows task and authenticated manual updates."""
    private = token_path().parent
    private.mkdir(parents=True, exist_ok=True)
    # Separate lock database prevents overlapping task instances without holding
    # a transaction on the listening-history database across network requests.
    with closing(sqlite3.connect(private / "spotify-job-lock.db", timeout=1)) as lock:
        try:
            lock.execute("BEGIN IMMEDIATE")
        except sqlite3.OperationalError:
            return {"status": "busy", "message": "A Spotify update is already running. Please try again shortly."}
        history = private / "spotify-history.db"
        catalog = Path(__file__).resolve().parents[3] / "portfolio.db"
        return run_job(catalog, history, SpotifyApi(), force=force, downloads=Path.home() / 'Downloads')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="Refresh the publication even if a week has not elapsed")
    args = parser.parse_args()
    report = run_local_job(force=args.refresh)
    if __import__("sys").stdout is not None:
        print(json.dumps(report, indent=2))
    if report["status"] in ("error", "waiting"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
