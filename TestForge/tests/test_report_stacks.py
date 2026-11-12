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


class ReportStacksTest(unittest.TestCase):
    def test_report_emits_per_stack_sections(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            results_path = root / "run-results.json"
            results_path.write_text(json.dumps({
                "summary": {
                    "total": 2, "passed": 1, "failed": 1, "timeout": 0,
                    "error": 0, "flaky": 0, "flaky_rate": 0.0,
                    "by_stack": {
                        "api": {"total": 1, "passed": 1, "failed": 0, "flaky": 0},
                        "web": {"total": 1, "passed": 0, "failed": 1, "flaky": 0},
                    },
                },
                "suites": [
                    {"name": "api-unit", "status": "passed", "duration_sec": 1, "command": "pytest", "stack_id": "api"},
                    {"name": "web-e2e", "status": "failed", "duration_sec": 2, "command": "playwright",
                     "stack_id": "web", "stderr": "selector missing"},
                ],
            }), encoding="utf-8")
            validation_path = root / "validation.json"
            validation_path.write_text(json.dumps({
                "summary": {
                    "total_cases": 3, "errors": 0, "warnings": 1, "duplicates": 0,
                    "max_similarity": 0.1, "automatable": 2,
                    "by_stack": {
                        "api": {"total": 2, "errors": 0, "warnings": 0},
                        "web": {"total": 1, "errors": 0, "warnings": 1},
                    },
                },
                "coverage": {"requirements": 2, "covered": 2, "uncovered": [], "ac_coverage": 1.0},
            }), encoding="utf-8")
            gate_path = root / "gate-report.json"
            gate_path.write_text(json.dumps({
                "passed": False,
                "checks": [
                    {"name": "api.line_coverage", "value": 0.8, "threshold": 0.6, "passed": True},
                    {"name": "web.line_coverage", "value": 0.4, "threshold": 0.6, "passed": False},
                ],
                "failures": [{"name": "web.line_coverage", "passed": False}],
                "stacks": {
                    "api": {"line_coverage": 0.8, "mutation_score": 0.7, "not_applicable": [], "passed": True},
                    "web": {"line_coverage": 0.4, "mutation_score": None, "not_applicable": ["mutation_score"], "passed": False},
                    "k8s": {"line_coverage": None, "mutation_score": None,
                            "not_applicable": ["line_coverage", "mutation_score"], "passed": True},
                },
            }), encoding="utf-8")
            out = root / "report.md"

            proc = run_cli(
                "report", "--results", str(results_path), "--validation", str(validation_path),
                "--gate", str(gate_path), "--out", str(out),
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            text = out.read_text(encoding="utf-8")
            self.assertIn("## Stack: api", text)
            self.assertIn("## Stack: web", text)
            self.assertIn("## Stack: k8s", text)
            self.assertIn("Line coverage: 0.8", text)
            self.assertIn("Not applicable: mutation_score", text)
            web_section = text.split("## Stack: web", 1)[1].split("## Stack: k8s", 1)[0]
            self.assertIn("web-e2e", web_section)
            self.assertIn("selector missing", web_section)
            self.assertIn("FAIL", web_section)
            self.assertIn("### Next actions", web_section)


if __name__ == "__main__":
    unittest.main()
