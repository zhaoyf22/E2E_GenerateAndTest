import tempfile
import unittest
from pathlib import Path

from core.packs import Pack
from core.prompt import compose_prompt


class PromptTest(unittest.TestCase):
    def test_composes_base_and_partial(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            prompts = root / "prompts"
            prompts.mkdir()
            (prompts / "02-test-design.md").write_text("# base prompt\n", encoding="utf-8")
            pack_dir = root / "packs" / "python-service"
            (pack_dir / "partials").mkdir(parents=True)
            (pack_dir / "partials" / "python.md").write_text("# python rules\n", encoding="utf-8")
            pack = Pack(
                id="python-service",
                path=pack_dir,
                manifest={"id": "python-service", "prompt_partials": ["partials/python.md"]},
            )
            config = {
                "project": {"type": "service"},
                "stacks": [{"id": "api", "pack": "python-service", "root": "services/api", "commands": {"unit": "pytest -q"}}],
            }
            text = compose_prompt("02-test-design", "api", config, {"python-service": pack}, prompts)
            self.assertIn("# base prompt", text)
            self.assertIn("# python rules", text)
            self.assertIn("stack_id: `api`", text)
            self.assertIn("pytest -q", text)

    def test_unknown_stage_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError):
                compose_prompt("missing", "api", {}, {}, Path(tmp))


if __name__ == "__main__":
    unittest.main()
