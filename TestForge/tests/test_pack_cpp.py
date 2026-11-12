import unittest
from pathlib import Path

from core.packs import load_pack

PACKS = Path(__file__).resolve().parents[1] / "packs"


class CppPackTest(unittest.TestCase):
    def test_manifest_contract(self):
        pack = load_pack(PACKS / "cpp-cli")
        self.assertTrue(pack.commands["unit"].startswith("ctest"))
        self.assertEqual(pack.coverage["parser"], "lcov")
        self.assertEqual(pack.mutation["tool"], "mull")
        template_ids = {item["id"] for item in pack.templates}
        self.assertTrue({"gtest", "catch2", "cmake", "mull", "fuzztest", "rapidcheck", "approvaltests", "cli11"}.issubset(template_ids))
        for item in pack.templates:
            self.assertTrue((pack.path / item["path"]).is_file(), item["path"])


if __name__ == "__main__":
    unittest.main()
