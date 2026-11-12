import tempfile
import unittest
from pathlib import Path

from core.detect import detect_stacks
from core.packs import Pack


def fake_pack(pack_id, files, globs=None):
    manifest = {"id": pack_id, "detect": {"files": files, "globs": globs or [], "priority": 10}}
    return Pack(id=pack_id, path=Path("."), manifest=manifest)


class DetectTest(unittest.TestCase):
    def test_detects_python_and_java_in_monorepo(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "services/api").mkdir(parents=True)
            (root / "services/api/pyproject.toml").write_text("", encoding="utf-8")
            (root / "services/order").mkdir(parents=True)
            (root / "services/order/pom.xml").write_text("", encoding="utf-8")
            packs = {
                "python-service": fake_pack("python-service", ["pyproject.toml"]),
                "java-service": fake_pack("java-service", ["pom.xml"]),
            }
            stacks = detect_stacks(root, packs)
            self.assertEqual(sorted((s.pack, s.root) for s in stacks), [
                ("java-service", "services/order"),
                ("python-service", "services/api"),
            ])

    def test_two_services_same_pack_get_unique_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ("a", "b"):
                (root / "services" / name).mkdir(parents=True)
                (root / "services" / name / "pyproject.toml").write_text("", encoding="utf-8")
            packs = {"python-service": fake_pack("python-service", ["pyproject.toml"])}
            stacks = detect_stacks(root, packs)
            self.assertEqual(len(stacks), 2)
            self.assertEqual(len({s.id for s in stacks}), 2)

    def test_glob_is_grouped_by_nearest_package_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "frontend/src").mkdir(parents=True)
            (root / "frontend/package.json").write_text("{}", encoding="utf-8")
            (root / "frontend/src/App.tsx").write_text("", encoding="utf-8")
            packs = {"frontend-web": fake_pack("frontend-web", ["package.json"], ["src/**/*.tsx"])}
            stacks = detect_stacks(root, packs)
            self.assertEqual([(s.pack, s.root) for s in stacks], [("frontend-web", "frontend")])


if __name__ == "__main__":
    unittest.main()
