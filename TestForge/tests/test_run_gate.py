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


class RunGateTest(unittest.TestCase):
    def test_run_dry_run_filters_report_suites(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".testforge").mkdir()
            manifest = {
                "suites": [
                    {"name": "api-unit", "command": f'"{sys.executable}" -c "print(1)"', "kind": "test", "stack_id": "api"},
                    {"name": "api-coverage", "command": f'"{sys.executable}" -c "print(2)"', "kind": "report", "run_after": ["api-unit"], "stack_id": "api"},
                ]
            }
            manifest_path = root / ".testforge" / "run-manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            proc = run_cli("run", "--manifest", str(manifest_path), "--dry-run")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            results = json.loads((root / ".testforge" / "runs" / "run-results.json").read_text(encoding="utf-8"))
            self.assertEqual([s["name"] for s in results["suites"]], ["api-unit"])

            proc = run_cli("run", "--manifest", str(manifest_path), "--dry-run", "--with-reports")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            results = json.loads((root / ".testforge" / "runs" / "run-results.json").read_text(encoding="utf-8"))
            self.assertEqual([s["name"] for s in results["suites"]], ["api-unit", "api-coverage"])

    def test_gate_missing_coverage_fails_and_can_be_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = {
                "project": {"name": "tmp", "type": "service", "root": "."},
                "stacks": [{"id": "api", "pack": "python-service", "root": "."}],
                "quality_gates": {"line_coverage_min": 0.6},
            }
            config_path = root / "testforge.config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            results_path = root / "run-results.json"
            results_path.write_text(json.dumps({
                "suites": [{"name": "unit", "status": "passed", "stack_id": "api"}],
                "summary": {"by_stack": {"api": {"total": 1, "passed": 1}}},
            }), encoding="utf-8")

            proc = run_cli("gate", "--results", str(results_path), "--config", str(config_path))
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("api.line_coverage", proc.stdout)

            proc = run_cli(
                "gate", "--results", str(results_path), "--config", str(config_path),
                "--allow-missing-reports",
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_gate_none_is_not_applicable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = {
                "project": {"name": "tmp", "type": "platform", "root": "."},
                "stacks": [{"id": "k8s", "pack": "k8s", "root": "."}],
            }
            config_path = root / "testforge.config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            results_path = root / "run-results.json"
            results_path.write_text(json.dumps({
                "suites": [{"name": "e2e", "status": "passed", "stack_id": "k8s"}],
                "summary": {"by_stack": {"k8s": {"total": 1, "passed": 1}}},
            }), encoding="utf-8")
            proc = run_cli("gate", "--results", str(results_path), "--config", str(config_path))
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()
