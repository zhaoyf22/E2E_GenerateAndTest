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


class StackContextTest(unittest.TestCase):
    def test_pack_collects_from_each_stack_root_and_dedupes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "services/api/docs").mkdir(parents=True)
            (root / "services/order/docs").mkdir(parents=True)
            (root / "services/api/docs/req.md").write_text("# API\n\napi requirement\n", encoding="utf-8")
            (root / "services/order/docs/req.md").write_text("# Order\n\norder requirement\n", encoding="utf-8")
            config = {
                "project": {"name": "tmp", "type": "platform", "root": "."},
                "stacks": [
                    {
                        "id": "api",
                        "pack": "python-service",
                        "root": "services/api",
                        "inputs": {"docs": ["docs/**/*.md"]},
                    },
                    {
                        "id": "svc",
                        "pack": "java-service",
                        "root": ".",
                        "inputs": {"docs": ["services/**/*.md"]},
                    },
                ],
            }
            config_path = root / "testforge.config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")

            proc = run_cli("pack", "--config", str(config_path), "--out", str(root / "ctx"))
            self.assertEqual(proc.returncode, 0, proc.stderr)

            payload = json.loads((root / "ctx" / "context.json").read_text(encoding="utf-8"))
            entries = payload["entries"]
            self.assertEqual({entry["stack_id"] for entry in entries}, {"api", "svc"})
            self.assertEqual({entry["pack"] for entry in entries}, {"java-service", "python-service"})
            files = [entry["file"] for entry in entries]
            self.assertEqual(files.count("services/api/docs/req.md"), 1)
            self.assertIn("services/order/docs/req.md", files)
            api_entry = next(entry for entry in entries if entry["file"] == "services/api/docs/req.md")
            self.assertEqual(api_entry["stack_id"], "api")
            self.assertEqual(api_entry["pack"], "python-service")

            context_md = (root / "ctx" / "context.md").read_text(encoding="utf-8")
            self.assertIn("## Stacks", context_md)

    def test_legacy_config_still_packs_global_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "docs/req.md").write_text("# Legacy\n\nlegacy requirement\n", encoding="utf-8")
            config_path = root / "testforge.config.json"
            config_path.write_text(json.dumps({
                "project": {"name": "legacy", "type": "service", "root": "."},
                "inputs": {"docs": ["docs/**/*.md"]},
            }), encoding="utf-8")

            proc = run_cli("pack", "--config", str(config_path), "--out", str(root / "ctx"))
            self.assertEqual(proc.returncode, 0, proc.stderr)
            payload = json.loads((root / "ctx" / "context.json").read_text(encoding="utf-8"))
            self.assertEqual(len(payload["entries"]), 1)
            self.assertEqual(payload["entries"][0]["stack_id"], "default")


if __name__ == "__main__":
    unittest.main()
