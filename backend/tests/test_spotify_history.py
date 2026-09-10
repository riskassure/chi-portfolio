from datetime import datetime, timezone
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from services.music.spotify_history import import_history, rank_history, six_months_before


class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.archive = Path(self.temp.name) / "history.zip"
        self.database = Path(self.temp.name) / "history.db"

    def write(self, rows):
        with zipfile.ZipFile(self.archive, "w") as archive:
            archive.writestr("Spotify/Streaming_History_Audio_2026.json", json.dumps(rows))
            archive.writestr("unrelated.json", '{"private": "never imported"}')

    def row(self, day, ms=30000, track="a"):
        return {"ts": day, "ms_played": ms, "spotify_track_uri": "spotify:track:" + track * 22,
                "ip_addr": "private", "platform": "private"}

    def test_repeat_import_and_minimal_storage(self):
        row = self.row("2026-09-01T00:00:00Z")
        self.write([row, row, {"spotify_track_uri": None}])
        self.assertEqual(import_history(self.archive, self.database)["inserted"], 1)
        self.assertEqual(import_history(self.archive, self.database)["stored_records"], 1)
        with closing(sqlite3.connect(self.database)) as connection:
            self.assertEqual([r[1] for r in connection.execute("PRAGMA table_info(spotify_history)")],
                             ["track_id", "ended_at", "ms_played"])

    def test_six_month_window_threshold_and_zero_duration(self):
        self.write([self.row("2026-03-10T00:00:00Z"), self.row("2026-03-09T23:59:59Z"),
                    self.row("2026-09-10T00:00:00Z"), self.row("2026-06-01T00:00:00Z", 29999),
                    self.row("2026-06-02T00:00:00Z", 0)])
        import_history(self.archive, self.database)
        end = datetime(2026, 9, 10, tzinfo=timezone.utc)
        self.assertEqual(rank_history(self.database, end)[0]["plays"], 1)
        self.assertEqual(rank_history(self.database, end, 1)[0]["plays"], 2)
        self.assertEqual(six_months_before(datetime(2024, 8, 31)).date().isoformat(), "2024-02-29")

    def test_bad_record_rolls_back(self):
        self.write([self.row("2026-09-01T00:00:00Z"), self.row("invalid")])
        with self.assertRaises(ValueError):
            import_history(self.archive, self.database)
        with closing(sqlite3.connect(self.database)) as connection:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM spotify_history").fetchone()[0], 0)


if __name__ == "__main__":
    unittest.main()
