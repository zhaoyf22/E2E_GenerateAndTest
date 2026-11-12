import unittest
from pathlib import Path

from core.packs import load_pack

PACKS = Path(__file__).resolve().parents[1] / "packs"


class PythonPackTest(unittest.TestCase):
    def test_manifest_contract(self):
        pack = load_pack(PACKS / "python-service")
        self.assertEqual(pack.id, "python-service")
        self.assertEqual(pack.commands["unit"], "pytest -q")
        self.assertEqual(pack.coverage["parser"], "coverage.py")
        self.assertEqual(pack.scaffold["default_template"], "pytest")
        template_ids = {item["id"] for item in pack.templates}
        self.assertTrue({"pytest", "conftest", "testcontainers", "schemathesis", "hypothesis"}.issubset(template_ids))
        for item in pack.templates:
            self.assertTrue((pack.path / item["path"]).is_file(), item["path"])

    def test_acceptance_exists(self):
        pack = load_pack(PACKS / "python-service")
        self.assertTrue((pack.path / pack.acceptance).is_file())


if __name__ == "__main__":
    unittest.main()
