import unittest
from pathlib import Path

from core.packs import load_pack

PACKS = Path(__file__).resolve().parents[1] / "packs"


class JavaPackTest(unittest.TestCase):
    def test_manifest_contract(self):
        pack = load_pack(PACKS / "java-service")
        self.assertEqual(pack.commands["unit"], "mvn -q test")
        self.assertEqual(pack.coverage["parser"], "jacoco")
        self.assertEqual(pack.mutation["parser"], "pit-xml")
        template_ids = {item["id"] for item in pack.templates}
        self.assertTrue({"junit5", "testcontainers", "wiremock", "restassured"}.issubset(template_ids))
        for item in pack.templates:
            self.assertTrue((pack.path / item["path"]).is_file(), item["path"])


if __name__ == "__main__":
    unittest.main()
