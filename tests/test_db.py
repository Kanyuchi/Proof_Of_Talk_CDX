from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from app import db


class DbTest(unittest.TestCase):
    def setUp(self) -> None:
        self._original = os.environ.get("DATABASE_URL")

    def tearDown(self) -> None:
        if self._original is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = self._original

    def test_parse_database_url_variants(self) -> None:
        self.assertEqual(db._parse_database_url("sqlite:///tmp/a.db").kind, "sqlite")
        self.assertEqual(db._parse_database_url("postgresql://u:p@h:5432/d").kind, "postgres")
        self.assertEqual(db._parse_database_url("mysql://u:p@h:3306/d").kind, "mysql")

    def test_sqlite_round_trip_actions(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "actions.db"
            os.environ["DATABASE_URL"] = f"sqlite:///{path}"
            db.init_db()
            db.upsert_action("p1", "p2", "approved", "test", "2026-02-17T00:00:00Z")
            rows = db.get_all_actions()
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["from_id"], "p1")
            self.assertEqual(rows[0]["to_id"], "p2")
            self.assertEqual(rows[0]["status"], "approved")

    def test_backend_summary_reports_current_backend(self) -> None:
        os.environ["DATABASE_URL"] = "sqlite:///tmp/summary.db"
        s = db.backend_summary()
        self.assertEqual(s["backend"], "sqlite")


if __name__ == "__main__":
    unittest.main()
