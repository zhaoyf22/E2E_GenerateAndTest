import subprocess
import tempfile
import unittest
from pathlib import Path

from core.packs import load_pack

PACKS = Path(__file__).resolve().parents[1] / "packs"


class PythonPackTest(unittest.TestCase):
    def test_manifest_contract(self):
        pack = load_pack(PACKS / "python-service")
        self.assertEqual(pack.id, "python-service")
        self.assertEqual(pack.commands["unit"], "python -m pytest -q --ignore=testforge")
        self.assertEqual(pack.coverage["parser"], "coverage.py")
        self.assertIn("mutmut export-cicd-stats", pack.commands["mutation"])
        self.assertEqual(pack.mutation["parser"], "mutmut")
        self.assertEqual(pack.mutation["report"], "mutants/mutmut-cicd-stats.json")
        self.assertEqual(pack.scaffold["default_template"], "pytest")
        template_ids = {item["id"] for item in pack.templates}
        self.assertTrue({"pytest", "conftest", "testcontainers", "schemathesis", "hypothesis"}.issubset(template_ids))
        for item in pack.templates:
            self.assertTrue((pack.path / item["path"]).is_file(), item["path"])

    def test_acceptance_exists(self):
        pack = load_pack(PACKS / "python-service")
        self.assertTrue((pack.path / pack.acceptance).is_file())


    def test_api_command_skips_missing_directory_but_runs_when_present(self):
        pack = load_pack(PACKS / "python-service")
        with tempfile.TemporaryDirectory() as tmp:
            proc = subprocess.run(
                pack.commands["api"], shell=True, cwd=tmp,
                capture_output=True, text=True, encoding="utf-8",
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            api = Path(tmp) / "tests" / "api"
            api.mkdir(parents=True)
            (api / "test_bad.py").write_text("def test_bad():\n    assert False\n", encoding="utf-8")
            proc = subprocess.run(
                pack.commands["api"], shell=True, cwd=tmp,
                capture_output=True, text=True, encoding="utf-8",
            )
            self.assertNotEqual(proc.returncode, 0)


if __name__ == "__main__":
    unittest.main()
