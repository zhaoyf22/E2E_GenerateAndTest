import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from testforge import load_mutation_score, parse_coverage

SUITE = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).resolve().parent / "fixtures"


def run_cli(*args):
    return subprocess.run(
        [sys.executable, str(SUITE / "testforge.py"), *args],
        cwd=str(SUITE), capture_output=True, text=True, encoding="utf-8",
    )


class ParserRoutingTest(unittest.TestCase):
    def test_coverage_parser_dispatch(self):
        self.assertAlmostEqual(
            parse_coverage(str(FIXTURES / "coverage_py.json"), "coverage.py"), 0.855, places=4
        )
        self.assertAlmostEqual(
            parse_coverage(str(FIXTURES / "gcovr-coverage.xml"), "gcovr"), 0.75, places=4
        )
        self.assertAlmostEqual(
            parse_coverage(str(FIXTURES / "istanbul-coverage-summary.json"), "istanbul"), 0.80, places=4
        )
        self.assertIsNone(parse_coverage(str(FIXTURES / "coverage_py.json"), "none"))

    def test_mutation_parser_dispatch(self):
        self.assertAlmostEqual(
            load_mutation_score(str(FIXTURES / "mutations.xml"), "pit-xml"), 0.5, places=4
        )
        self.assertAlmostEqual(
            load_mutation_score(str(FIXTURES / "mutmut-cicd-stats.json"), "mutmut"), 0.8, places=4
        )
        self.assertAlmostEqual(
            load_mutation_score(str(FIXTURES / "mull-report.json"), "json"), 0.75, places=4
        )
        self.assertIsNone(load_mutation_score(str(FIXTURES / "mutmut-cicd-stats.json"), "none"))


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
            report = json.loads((root / "gate-report.json").read_text(encoding="utf-8"))
            self.assertEqual(
                report["stacks"]["k8s"]["not_applicable"], ["line_coverage", "mutation_score"]
            )
            self.assertTrue(report["stacks"]["k8s"]["passed"])

    def test_legacy_config_with_passing_results_and_no_reports_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = root / "testforge.config.json"
            config_path.write_text(json.dumps({
                "project": {"name": "legacy", "type": "service", "root": "."},
                "commands": {"unit": "pytest -q"},
                "inputs": {"docs": ["docs/**/*.md"], "code": ["src/**/*.py"]},
            }), encoding="utf-8")
            results_path = root / "run-results.json"
            results_path.write_text(json.dumps({
                "suites": [{"name": "unit", "status": "passed"}],
                "summary": {"total": 1, "passed": 1, "flaky_rate": 0.0},
            }), encoding="utf-8")
            proc = run_cli("gate", "--results", str(results_path), "--config", str(config_path))
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            report = json.loads((root / "gate-report.json").read_text(encoding="utf-8"))
            self.assertEqual(
                report["stacks"]["default"]["not_applicable"], ["line_coverage", "mutation_score"]
            )

    def test_legacy_xml_reports_infer_parser(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copy(FIXTURES / "gcovr-coverage.xml", root / "coverage.xml")
            shutil.copy(FIXTURES / "mutations.xml", root / "mutations.xml")
            config_path = root / "testforge.config.json"
            config_path.write_text(json.dumps({
                "project": {"name": "legacy", "type": "service", "root": "."},
                "paths": {
                    "coverage_report": "coverage.xml",
                    "mutation_report": "mutations.xml",
                },
                "quality_gates": {"line_coverage_min": 0.5, "mutation_score_min": 0.4},
            }), encoding="utf-8")
            results_path = root / "run-results.json"
            results_path.write_text(json.dumps({
                "suites": [{"name": "unit", "status": "passed"}],
                "summary": {"total": 1, "passed": 1, "flaky_rate": 0.0},
            }), encoding="utf-8")
            proc = run_cli("gate", "--results", str(results_path), "--config", str(config_path))
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            report = json.loads((root / "gate-report.json").read_text(encoding="utf-8"))
            self.assertAlmostEqual(report["stacks"]["default"]["line_coverage"], 0.75, places=3)
            self.assertAlmostEqual(report["stacks"]["default"]["mutation_score"], 0.5, places=3)

    def test_gate_stack_outcomes_use_parser_routing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = {
                "project": {"name": "tmp", "type": "platform", "root": "."},
                "stacks": [
                    {
                        "id": "api",
                        "pack": "python-service",
                        "root": ".",
                        "coverage": {"parser": "coverage.py", "report": str(FIXTURES / "coverage_py.json")},
                        "mutation": {"parser": "pit-xml", "report": str(FIXTURES / "mutations.xml")},
                    },
                    {"id": "k8s", "pack": "k8s", "root": "."},
                ],
            }
            config_path = root / "testforge.config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            results_path = root / "run-results.json"
            results_path.write_text(json.dumps({
                "suites": [
                    {"name": "api-unit", "status": "passed", "stack_id": "api"},
                    {"name": "k8s-e2e", "status": "passed", "stack_id": "k8s"},
                ],
                "summary": {"by_stack": {"api": {"total": 1, "passed": 1}, "k8s": {"total": 1, "passed": 1}}},
            }), encoding="utf-8")
            proc = run_cli("gate", "--results", str(results_path), "--config", str(config_path))
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            report = json.loads((root / "gate-report.json").read_text(encoding="utf-8"))
            self.assertAlmostEqual(report["stacks"]["api"]["line_coverage"], 0.855, places=3)
            self.assertAlmostEqual(report["stacks"]["api"]["mutation_score"], 0.5, places=3)
            self.assertTrue(report["stacks"]["api"]["passed"])
            self.assertEqual(report["stacks"]["k8s"]["not_applicable"], ["line_coverage", "mutation_score"])
            self.assertEqual(report["suite_summary"]["api"]["total"], 1)
            names = {check["name"] for check in report["checks"]}
            self.assertIn("api.line_coverage", names)
            self.assertIn("api.mutation_score", names)

    def test_gate_parser_without_report_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = {
                "project": {"name": "tmp", "type": "service", "root": "."},
                "stacks": [{
                    "id": "api",
                    "pack": "python-service",
                    "root": ".",
                    "coverage": {"parser": "coverage.py", "report": ""},
                }],
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
            self.assertIn("missing report path", proc.stdout)
            proc = run_cli(
                "gate", "--results", str(results_path), "--config", str(config_path),
                "--allow-missing-reports",
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()
