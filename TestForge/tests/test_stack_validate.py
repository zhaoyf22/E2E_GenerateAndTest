import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SUITE = Path(__file__).resolve().parents[1]


def run_cli(*args):
    return subprocess.run(
        [sys.executable, str(SUITE / "testforge.py"), *args],
        cwd=str(SUITE), capture_output=True, text=True, encoding="utf-8",
    )


def case(case_id, stack_id, title):
    return {
        "id": case_id,
        "title": title,
        "stack_id": stack_id,
        "ac_ids": ["AC-001"],
        "source_refs": ["DOC-0001"],
        "technique": "EP",
        "priority": "P1",
        "type": "functional",
        "preconditions": [],
        "steps": [{"action": "do the thing", "expected": "it works"}],
        "expected_result": "the thing works",
        "automatable": True,
    }


class StackValidateTest(unittest.TestCase):
    def test_by_stack_summary_and_filter(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cases_path = root / "test-cases.json"
            cases_path.write_text(json.dumps({"test_cases": [
                case("TC-API", "api", "API case works"),
                case("TC-WEB", "web", "Web case works"),
            ]}), encoding="utf-8")

            out = root / "validation.json"
            proc = run_cli("validate", "--cases", str(cases_path), "--out", str(out))
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            report = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(set(report["summary"]["by_stack"]), {"api", "web"})
            self.assertEqual(report["summary"]["by_stack"]["api"]["total"], 1)
            self.assertEqual(report["summary"]["total_cases"], 2)

            proc = run_cli("validate", "--cases", str(cases_path), "--stack", "api", "--out", str(out))
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            report = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(report["summary"]["total_cases"], 1)
            self.assertEqual(set(report["summary"]["by_stack"]), {"api"})

    def test_errors_carry_stack_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            broken = case("TC-BAD", "svc", "Broken case title")
            broken["expected_result"] = ""
            cases_path = root / "test-cases.json"
            cases_path.write_text(json.dumps({"test_cases": [broken]}), encoding="utf-8")
            out = root / "validation.json"
            proc = run_cli("validate", "--cases", str(cases_path), "--out", str(out))
            self.assertEqual(proc.returncode, 1)
            report = json.loads(out.read_text(encoding="utf-8"))
            self.assertTrue(report["errors"])
            for item in report["errors"]:
                self.assertEqual(item.get("stack_id"), "svc")


if __name__ == "__main__":
    unittest.main()
