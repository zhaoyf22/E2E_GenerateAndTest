import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from core.packs import load_pack, load_packs

SUITE = Path(__file__).resolve().parents[1]
PACKS = SUITE / "packs"


class StubPackTest(unittest.TestCase):
    def test_all_five_packs_load(self):
        packs = load_packs(PACKS)
        self.assertEqual(sorted(packs), ["cpp-cli", "frontend-web", "java-service", "k8s", "python-service"])

    def test_frontend_and_k8s_have_no_coverage(self):
        self.assertEqual(load_pack(PACKS / "frontend-web").coverage["parser"], "istanbul")
        self.assertEqual(load_pack(PACKS / "k8s").coverage["parser"], "none")
        self.assertEqual(load_pack(PACKS / "k8s").mutation["parser"], "none")

    def test_init_dry_run_lists_stub_stack(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = subprocess.run(
                [sys.executable, str(SUITE / "testforge.py"), "init", "--stack", "frontend-web", "--target", tmp, "--dry-run"],
                cwd=str(SUITE), capture_output=True, text=True, encoding="utf-8",
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertEqual(payload["stacks"][0]["pack"], "frontend-web")


if __name__ == "__main__":
    unittest.main()
