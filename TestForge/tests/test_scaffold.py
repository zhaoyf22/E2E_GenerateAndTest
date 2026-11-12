import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from core.packs import Pack
from core.scaffold import scaffold_cases

SUITE = Path(__file__).resolve().parents[1]


class ScaffoldTest(unittest.TestCase):
    def make_pack(self, root: Path) -> Pack:
        pack_dir = root / "pack"
        (pack_dir / "templates").mkdir(parents=True)
        (pack_dir / "templates" / "pytest_test.py").write_text(
            '"""${id} ${title}"""\n\n# ${steps}\n# Expected: ${expected}\n',
            encoding="utf-8",
        )
        manifest = {
            "id": "python-service",
            "templates": [{"id": "pytest", "path": "templates/pytest_test.py", "target": "tests/test_${module}.py"}],
            "scaffold": {"default_template": "pytest"},
        }
        return Pack(id="python-service", path=pack_dir, manifest=manifest)

    def test_writes_one_file_per_case_and_skips_existing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pack = self.make_pack(root)
            cases = [
                {"id": "TC-1", "title": "first", "type": "functional", "steps": [{"action": "do it", "expected": "ok"}], "expected_result": "ok"},
                {"id": "TC-2", "title": "second", "type": "functional", "steps": [{"action": "do it", "expected": "ok"}], "expected_result": "ok"},
            ]
            out = root / "out"
            manifest = scaffold_cases(cases, pack, "api", out)
            self.assertEqual(len(manifest["written"]), 2)
            self.assertTrue((out / "tests" / "test_tc_1.py").exists())
            self.assertTrue((out / "tests" / "test_tc_2.py").exists())
            text = (out / "tests" / "test_tc_1.py").read_text(encoding="utf-8")
            self.assertIn("TC-1", text)
            self.assertIn("first", text)

            second = scaffold_cases(cases, pack, "api", out)
            self.assertEqual(len(second["written"]), 0)
            self.assertEqual(len(second["skipped"]), 2)
            self.assertTrue((out / "scaffold-manifest.json").exists())

    def test_force_overwrites(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pack = self.make_pack(root)
            case = {"id": "TC-1", "title": "first", "type": "functional", "steps": [], "expected_result": "ok"}
            out = root / "out"
            scaffold_cases([case], pack, "api", out)
            target = out / "tests" / "test_tc_1.py"
            target.write_text("old", encoding="utf-8")
            manifest = scaffold_cases([case], pack, "api", out, force=True)
            self.assertEqual(len(manifest["written"]), 1)
            self.assertNotEqual(target.read_text(encoding="utf-8"), "old")

    def test_cli_writes_manifest_under_testforge(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            proc = subprocess.run(
                [sys.executable, str(SUITE / "testforge.py"), "init",
                 "--profile", "python-service", "--target", str(root)],
                cwd=str(SUITE), capture_output=True, text=True, encoding="utf-8",
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            cases = root / "cases.json"
            cases.write_text(json.dumps({"test_cases": [{
                "id": "TC-1", "title": "first", "stack_id": "api", "type": "functional",
                "steps": [{"action": "do", "expected": "ok"}], "expected_result": "ok",
            }]}), encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, str(SUITE / "testforge.py"), "scaffold",
                 "--config", str(root / "testforge.config.json"),
                 "--cases", str(cases), "--stack", "api", "--out", "generated"],
                cwd=str(root), capture_output=True, text=True, encoding="utf-8",
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertTrue((root / ".testforge" / "scaffold-manifest.json").is_file())
            self.assertFalse((root / "generated" / "scaffold-manifest.json").exists())


if __name__ == "__main__":
    unittest.main()
