"""Import completed Spotify ZIP downloads; never move or extract the originals."""
from contextlib import closing
import hashlib
from pathlib import Path
import re
import sqlite3
import time
import zipfile

from services.music.spotify_history import import_history
from services.music.spotify_sync import connect


def import_downloads(downloads, history, now=None):
    now = time.time() if now is None else now
    report = {"imported": 0, "already_processed": 0, "deferred": 0, "issues": []}
    with closing(connect(history)) as db, db:
        db.execute("""CREATE TABLE IF NOT EXISTS history_archives (
            digest TEXT PRIMARY KEY, filename TEXT NOT NULL, imported_at REAL NOT NULL)""")
        processed = {row[0] for row in db.execute("SELECT digest FROM history_archives")}
    folder = Path(downloads)
    if not folder.is_dir():
        report["issues"].append("Downloads folder is unavailable.")
        return report
    for path in sorted(folder.iterdir()):
        if path.suffix.lower() != '.zip' or 'spotify' not in path.name.lower() or not path.is_file():
            continue
        try:
            stat = path.stat()
            if now - stat.st_mtime < 60 or any(Path(str(path) + ext).exists() for ext in ('.crdownload', '.part', '.tmp')):
                report["deferred"] += 1
                continue
            if stat.st_size > 512 * 1024 * 1024:
                raise ValueError('Archive too large')
            with path.open('rb') as stream:
                digest = hashlib.file_digest(stream, 'sha256').hexdigest()
                if digest in processed:
                    report["already_processed"] += 1
                    continue
                after = path.stat()
                if (stat.st_size, stat.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                    report["deferred"] += 1
                    continue
                stream.seek(0)
                with zipfile.ZipFile(stream) as archive:
                    if not any(re.fullmatch(r'Streaming_History_(Audio|Video)_.+\.json', Path(name).name) for name in archive.namelist()):
                        report["issues"].append(f"{path.name}: no Extended Streaming History found.")
                        continue
                stream.seek(0)
                def record_import(connection):
                    connection.execute('INSERT OR IGNORE INTO history_archives VALUES (?, ?, ?)',
                                       (digest, path.name, now))
                    connection.execute("INSERT OR REPLACE INTO sync_state VALUES ('history_publication_pending', '1')")
                import_history(stream, history, on_import=record_import)
                processed.add(digest)
                report["imported"] += 1
        except (OSError, ValueError, KeyError, TypeError, RuntimeError, zipfile.BadZipFile, EOFError):
            report["issues"].append(f"{path.name}: could not import; the file was left untouched. Download a complete Extended Streaming History ZIP and retry.")
    return report
