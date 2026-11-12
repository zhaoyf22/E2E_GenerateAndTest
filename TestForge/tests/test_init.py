import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SUITE = Path(__file__).resolve().parents[1]


def run_init(*args):
    return subprocess.run(
        [sys.executable, str(SUITE / "testforge.py"), "init", *args],
        cwd=str(SUITE), capture_output=True, text=True, encoding="utf-8",
    )


class InitTest(unittest.TestCase):
    def test_list_packs_lists_five(self):
        proc = run_init("--list-packs")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        for pack_id in ("frontend-web", "python-service", "java-service", "cpp-cli", "k8s"):
            self.assertIn(pack_id, proc.stdout)

    def test_dry_run_profile_python(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = run_init("--profile", "python-service", "--target", tmp, "--dry-run")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertEqual(payload["stacks"][0]["id"], "api")
            self.assertEqual(payload["stacks"][0]["pack"], "python-service")
            names = {suite["name"] for suite in payload["run_manifest"]["suites"]}
            self.assertIn("api-unit", names)
            self.assertIn("api-coverage", names)
            coverage = next(s for s in payload["run_manifest"]["suites"] if s["name"] == "api-coverage")
            self.assertEqual(coverage["kind"], "report")
            self.assertEqual(coverage["run_after"], ["api-unit"])

    def test_dry_run_detect_monorepo(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = Path(tmp) / "services" / "api"
            api.mkdir(parents=True)
            (api / "pyproject.toml").write_text("", encoding="utf-8")
            proc = run_init("--detect", "--target", tmp, "--dry-run")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            payload = json.loads(proc.stdout)
            stacks = {(s["pack"], s["root"]) for s in payload["stacks"]}
            self.assertIn(("python-service", "services/api"), stacks)

    def test_old_profile_service_still_works(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = run_init("--profile", "service", "--target", tmp, "--dry-run")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertEqual(payload["stacks"][0]["pack"], "python-service")

    def test_dry_run_does_not_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = run_init("--stack", "python-service", "--target", tmp, "--dry-run")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertFalse((Path(tmp) / "testforge.config.json").exists())
            self.assertFalse((Path(tmp) / ".testforge").exists())

    def test_upgrade_preserves_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = run_init("--profile", "python-service", "--target", tmp)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            config_path = Path(tmp) / "testforge.config.json"
            config = json.loads(config_path.read_text(encoding="utf-8"))
            config["project"]["name"] = "custom-name"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            proc = run_init("--profile", "python-service", "--target", tmp, "--upgrade")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            updated = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertEqual(updated["project"]["name"], "custom-name")

    def test_profile_pack_ids_match_acceptance(self):
        expected = {
            "python-service": "api",
            "java-service": "svc",
            "cpp-cli": "cli",
        }
        for profile, stack_id in expected.items():
            with tempfile.TemporaryDirectory() as tmp:
                proc = run_init("--profile", profile, "--target", tmp, "--dry-run")
                self.assertEqual(proc.returncode, 0, proc.stderr)
                payload = json.loads(proc.stdout)
                self.assertEqual(payload["stacks"][0]["id"], stack_id)
                self.assertEqual(payload["stacks"][0]["pack"], profile)

    def test_legacy_service_profile_detects_java(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "pom.xml").write_text("", encoding="utf-8")
            proc = run_init("--profile", "service", "--target", tmp, "--dry-run")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            payload = json.loads(proc.stdout)
            stack = payload["stacks"][0]
            self.assertEqual(stack["pack"], "java-service")
            self.assertEqual(stack["commands"]["unit"], "mvn -q test")
            self.assertTrue(stack["commands"]["mutation"].startswith("mvn "))
            self.assertIn("src/main/java/**/*.java", stack["inputs"]["code"])

    def test_legacy_service_profile_detects_python(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "pyproject.toml").write_text("", encoding="utf-8")
            proc = run_init("--profile", "backend", "--target", tmp, "--dry-run")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            payload = json.loads(proc.stdout)
            stack = payload["stacks"][0]
            self.assertEqual(stack["pack"], "python-service")
            self.assertIn("mutmut export-cicd-stats", stack["commands"]["mutation"])

    def test_legacy_cli_profile_keeps_extra_cli_smoke(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = run_init("--profile", "cli", "--target", tmp, "--dry-run")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            payload = json.loads(proc.stdout)
            stack = payload["stacks"][0]
            self.assertEqual(stack["pack"], "python-service")
            self.assertEqual(stack["commands"]["cli-smoke"], "python -m your_cli --help")
            self.assertEqual(stack["commands"]["unit"], "python -m pytest -q --ignore=testforge")

    def test_platform_profile_does_not_merge_legacy_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = run_init("--profile", "platform", "--target", tmp, "--dry-run")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertEqual(payload["config"]["inputs"]["code"], ["src/**/*.py"])
            by_pack = {stack["pack"]: stack for stack in payload["config"]["stacks"]}
            self.assertEqual(
                set(by_pack),
                {"frontend-web", "python-service", "java-service", "cpp-cli", "k8s"},
            )
            self.assertEqual(by_pack["k8s"]["kind"], "surface")

    def test_stack_id_assigns_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = run_init(
                "--target", tmp,
                "--stack", "python-service:services/api",
                "--stack", "java-service:services/order",
                "--stack-id", "api", "--stack-id", "svc",
                "--dry-run",
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertEqual([stack["id"] for stack in payload["stacks"]], ["api", "svc"])

    def test_with_ci_installs_pack_workflow(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = run_init("--profile", "python-service", "--target", tmp, "--with-ci")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            workflows = list((Path(tmp) / ".github" / "workflows").glob("testforge-*.yml"))
            self.assertEqual(len(workflows), 1)
            text = workflows[0].read_text(encoding="utf-8")
            self.assertIn("actions/setup-python", text)
            self.assertIn("Run manifest", text)
            self.assertIn("--stack ", text)
            self.assertNotIn("__STACK_ID__", text)
            self.assertIn("--allow-missing-reports", text)
            self.assertIn("testforge.py gate", text)
            self.assertNotIn("|| true", text)

    def test_with_ci_scopes_each_stack_workflow(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = run_init(
                "--target", tmp, "--with-ci",
                "--stack", "python-service:services/api",
                "--stack", "java-service:services/order",
                "--stack-id", "api", "--stack-id", "svc",
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            workflows = Path(tmp) / ".github" / "workflows"
            api = (workflows / "testforge-api.yml").read_text(encoding="utf-8")
            svc = (workflows / "testforge-svc.yml").read_text(encoding="utf-8")
            self.assertIn("--stack api", api)
            self.assertIn("--stack svc", svc)
            self.assertNotIn("--stack api", svc)
            self.assertNotIn("--stack svc", api)
            self.assertNotIn("__STACK_ID__", api + svc)

    def test_run_manifest_cwd_uses_posix_separators(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = run_init("--target", tmp, "--stack", "python-service:services/api", "--dry-run")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            payload = json.loads(proc.stdout)
            cwds = {suite["cwd"] for suite in payload["run_manifest"]["suites"]}
            self.assertTrue(cwds)
            for cwd in cwds:
                self.assertNotIn("\\", cwd)
                self.assertEqual(cwd, "../services/api")


if __name__ == "__main__":
    unittest.main()
