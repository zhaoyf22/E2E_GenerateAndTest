import json
import tempfile
import unittest
from pathlib import Path

from core.packs import get_pack, load_pack, load_packs, validate_pack


class PackTest(unittest.TestCase):
    def test_load_pack_reads_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            pack_dir = Path(tmp)
            (pack_dir / "pack.json").write_text(json.dumps({
                "id": "python-service",
                "display_name": "Python Service",
                "commands": {"unit": "pytest -q"},
                "inputs": {"code": ["src/**/*.py"]},
                "tools": [{"name": "pytest", "command": "pytest --version", "required": True}],
                "scaffold": {"default_template": "pytest"},
                "coverage": {"parser": "coverage.py", "report": "coverage.json"},
                "mutation": {"parser": "json", "report": "mutation-report.json", "score_key": "mutation_score"},
            }), encoding="utf-8")
            pack = load_pack(pack_dir)
            self.assertEqual(pack.id, "python-service")
            self.assertEqual(pack.commands["unit"], "pytest -q")
            self.assertEqual(pack.coverage["parser"], "coverage.py")
            self.assertEqual(pack.tools[0]["name"], "pytest")

    def test_load_packs_returns_all(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ("python-service", "java-service"):
                pack_dir = root / name
                pack_dir.mkdir()
                (pack_dir / "pack.json").write_text(json.dumps({"id": name}), encoding="utf-8")
            packs = load_packs(root)
            self.assertEqual(sorted(packs), ["java-service", "python-service"])
            self.assertIs(get_pack(packs, "python-service"), packs["python-service"])

    def test_validate_pack_reports_bad_types(self):
        errors = validate_pack({"id": "x", "commands": [], "inputs": []})
        self.assertTrue(any("commands" in e for e in errors))
        self.assertTrue(any("inputs" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
