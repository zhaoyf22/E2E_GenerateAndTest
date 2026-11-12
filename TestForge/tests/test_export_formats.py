import csv
import tempfile
import unittest
from pathlib import Path

from core.export_formats import TESTRAIL_HEADER, XRAY_HEADER, export_testrail_csv, export_xray_csv


CASES = [
    {
        "id": "TC-1",
        "title": "login works",
        "stack_id": "api",
        "feature": "Auth",
        "type": "functional",
        "priority": "P0",
        "preconditions": ["user exists"],
        "steps": [{"action": "login", "expected": "dashboard"}],
        "expected_result": "dashboard",
        "source_refs": ["DOC-1"],
        "ac_ids": ["AC-1"],
        "tags": ["smoke"],
    }
]


class ExportFormatsTest(unittest.TestCase):
    def test_testrail_header_and_row(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "testrail.csv"
            export_testrail_csv(CASES, out)
            rows = list(csv.reader(out.read_text(encoding="utf-8-sig").splitlines()))
            self.assertEqual(rows[0], TESTRAIL_HEADER)
            self.assertEqual(rows[1][0], "TC-1")
            self.assertEqual(rows[1][2], "api/Auth")
            self.assertIn("1. login", rows[1][6])

    def test_xray_header_and_row(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "xray.csv"
            export_xray_csv(CASES, out)
            rows = list(csv.reader(out.read_text(encoding="utf-8-sig").splitlines()))
            self.assertEqual(rows[0], XRAY_HEADER)
            self.assertEqual(rows[1][0], "TC-1")
            self.assertEqual(rows[1][7], "AC-1")


if __name__ == "__main__":
    unittest.main()
