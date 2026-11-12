import json
import tempfile
import unittest
from pathlib import Path

from core.config import load_config, normalize_stacks, project_root, stack_root
from core.packs import Pack


def fake_pack(pack_id, commands=None, inputs=None, coverage=None, mutation=None):
    return Pack(
        id=pack_id,
        path=Path("."),
        manifest={
            "id": pack_id,
            "commands": commands or {},
            "inputs": inputs or {},
            "coverage": coverage or {},
            "mutation": mutation or {},
        },
    )


class ConfigTest(unittest.TestCase):
    def test_old_config_without_stacks_synthesizes_default(self):
        config = {"project": {"type": "service", "root": "."}, "commands": {"unit": "pytest -q"}}
        stacks = normalize_stacks(config, packs={})
        self.assertEqual(len(stacks), 1)
        self.assertEqual(stacks[0]["id"], "default")
        self.assertEqual(stacks[0]["pack"], "python-service")
        self.assertEqual(stacks[0]["commands"]["unit"], "pytest -q")

    def test_explicit_stacks_keep_ids_and_roots(self):
        config = {
            "project": {"type": "platform", "root": "."},
            "stacks": [
                {"id": "api", "pack": "python-service", "root": "services/api"},
                {"id": "svc", "pack": "java-service", "root": "services/order"},
            ],
        }
        stacks = normalize_stacks(config, packs={})
        self.assertEqual([s["id"] for s in stacks], ["api", "svc"])
        self.assertEqual(stacks[0]["root"], "services/api")

    def test_stack_merges_pack_commands_and_overrides(self):
        packs = {
            "python-service": fake_pack(
                "python-service",
                commands={"unit": "pytest -q", "coverage": "pytest --cov=src"},
                coverage={"parser": "coverage.py", "report": "coverage.json"},
            )
        }
        config = {
            "project": {"type": "platform", "root": "."},
            "stacks": [
                {
                    "id": "api",
                    "pack": "python-service",
                    "root": "services/api",
                    "commands": {"unit": "uv run pytest -q"},
                }
            ],
        }
        stacks = normalize_stacks(config, packs)
        self.assertEqual(stacks[0]["commands"]["unit"], "uv run pytest -q")
        self.assertEqual(stacks[0]["commands"]["coverage"], "pytest --cov=src")
        self.assertEqual(stacks[0]["coverage"]["parser"], "coverage.py")

    def test_duplicate_stack_ids_are_rejected(self):
        config = {
            "project": {"type": "platform"},
            "stacks": [
                {"id": "api", "pack": "python-service"},
                {"id": "api", "pack": "java-service"},
            ],
        }
        with self.assertRaises(ValueError):
            normalize_stacks(config, packs={})

    def test_stack_root_uses_project_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = root / "testforge.config.json"
            config_path.write_text(
                json.dumps({
                    "project": {"root": "."},
                    "stacks": [{"id": "api", "pack": "python-service", "root": "services/api"}],
                }),
                encoding="utf-8",
            )
            config = load_config(str(config_path))
            stack = normalize_stacks(config, packs={})[0]
            self.assertEqual(stack_root(config, stack, str(config_path)), root / "services/api")
            self.assertEqual(project_root(config, str(config_path)), root)


if __name__ == "__main__":
    unittest.main()
