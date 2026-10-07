"""Regression checks for COPY replay handling, without a Snowflake connection."""

from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ingestion"))
from load_month import copy_month


class CopyMonthTests(unittest.TestCase):
    def cursor(self, result, count=3475226):
        cursor = MagicMock()
        cursor.fetchall.return_value = [result]
        cursor.fetchone.return_value = {
            "TRIP_COUNT": count, "MISSING_LOADED_AT": 0,
            "FIRST_LOADED_AT": "2026-10-07", "LAST_LOADED_AT": "2026-10-07",
        }
        return cursor

    def test_already_loaded_message_still_verifies_raw(self):
        cursor = self.cursor({
            "status": "LOAD_SKIPPED", "errors_seen": 1,
            "first_error": "File was loaded before.", "rows_loaded": 0,
        })
        copy_month(cursor, "yellow_tripdata_2025-01.parquet")
        self.assertIn("SELECT COUNT(*)", cursor.execute.call_args.args[0])
        self.assertEqual(cursor.execute.call_args.args[1],
                         ("yellow_tripdata_2025-01.parquet",))
        cursor.fetchone.assert_called_once()

    def test_other_skip_error_is_rejected(self):
        cursor = self.cursor({
            "status": "LOAD_SKIPPED", "errors_seen": 1,
            "first_error": "Invalid Parquet file",
        })
        with self.assertRaisesRegex(RuntimeError, "COPY reported errors"):
            copy_month(cursor, "yellow_tripdata_2025-01.parquet")
        cursor.fetchone.assert_not_called()

    def test_loaded_with_errors_is_rejected(self):
        cursor = self.cursor({"status": "LOADED", "errors_seen": 1})
        with self.assertRaisesRegex(RuntimeError, "COPY reported errors"):
            copy_month(cursor, "yellow_tripdata_2025-01.parquet")

    def test_skip_cannot_hide_missing_raw_rows(self):
        cursor = self.cursor({
            "status": "LOAD_SKIPPED", "errors_seen": 1,
            "first_error": "File was loaded before.",
        }, count=0)
        with self.assertRaisesRegex(RuntimeError, "RAW verification failed"):
            copy_month(cursor, "yellow_tripdata_2025-01.parquet")

    def test_successful_load_is_accepted(self):
        cursor = self.cursor({"status": "LOADED", "errors_seen": 0})
        copy_month(cursor, "yellow_tripdata_2025-01.parquet")
        cursor.fetchone.assert_called_once()


if __name__ == "__main__":
    unittest.main()
