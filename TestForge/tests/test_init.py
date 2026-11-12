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


if __name__ == "__main__":
    unittest.main()
