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


def case(case_id, stack_id, ac_id):
    return {
        "id": case_id,
        "title": f"{case_id} title",
        "stack_id": stack_id,
        "ac_ids": [ac_id],
        "source_refs": ["DOC-0001"],
        "technique": "EP",
        "priority": "P1",
        "type": "functional",
        "preconditions": [],
        "steps": [{"action": "do the thing", "expected": "it works"}],
        "expected_result": "the thing works",
        "automatable": True,
    }


class StackMatrixTest(unittest.TestCase):
    def test_two_acs_two_stacks_seed_all_combinations(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            requirements = root / "requirements.json"
            requirements.write_text(json.dumps([
                {"ac_id": "AC-001", "text": "first"},
                {"ac_id": "AC-002", "text": "second"},
            ]), encoding="utf-8")
            cases = root / "test-cases.json"
            cases.write_text(json.dumps({"test_cases": [
                case("TC-1", "api", "AC-001"),
                case("TC-2", "web", "AC-002"),
            ]}), encoding="utf-8")
            config = root / "testforge.config.json"
            config.write_text(json.dumps({
                "project": {"name": "tmp", "type": "platform", "root": "."},
                "stacks": [
                    {"id": "api", "pack": "python-service", "root": "."},
                    {"id": "web", "pack": "frontend-web", "root": "."},
                ],
            }), encoding="utf-8")
            out = root / "matrix.json"

            proc = run_cli(
                "matrix", "--cases", str(cases), "--requirements", str(requirements),
                "--config", str(config), "--out", str(out),
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            payload = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(payload["matrix_by_stack"]["AC-001"]["api"], ["TC-1"])
            self.assertEqual(payload["matrix_by_stack"]["AC-001"]["web"], [])
            self.assertEqual(payload["matrix_by_stack"]["AC-002"]["web"], ["TC-2"])
            self.assertEqual(payload["matrix_by_stack"]["AC-002"]["api"], [])
            self.assertEqual(payload["uncovered_by_stack"]["AC-001"], ["web"])
            self.assertEqual(payload["uncovered_by_stack"]["AC-002"], ["api"])
            self.assertEqual(payload["uncovered"], [])

            markdown = out.with_suffix(".md").read_text(encoding="utf-8")
            self.assertIn("| AC | api | web |", markdown)
            self.assertIn("| AC-001 | TC-1 | **UNCOVERED** |", markdown)

    def test_stack_filter_limits_columns(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            requirements = root / "requirements.json"
            requirements.write_text(json.dumps([{"ac_id": "AC-001", "text": "first"}]), encoding="utf-8")
            cases = root / "test-cases.json"
            cases.write_text(json.dumps({"test_cases": [
                case("TC-1", "api", "AC-001"),
                case("TC-2", "web", "AC-001"),
            ]}), encoding="utf-8")
            out = root / "matrix.json"
            proc = run_cli(
                "matrix", "--cases", str(cases), "--requirements", str(requirements),
                "--stack", "api", "--out", str(out),
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            payload = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(payload["matrix_by_stack"]["AC-001"], {"api": ["TC-1"]})
            self.assertEqual(payload["uncovered_by_stack"]["AC-001"], [])


if __name__ == "__main__":
    unittest.main()
