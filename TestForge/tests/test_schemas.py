import importlib.util
import json
import unittest
from pathlib import Path

SUITE = Path(__file__).resolve().parents[1]
SCHEMAS = SUITE / "schemas"
EXAMPLES = SUITE / "examples"


def load(name):
    return json.loads((SCHEMAS / name).read_text(encoding="utf-8"))


class SchemaTest(unittest.TestCase):
    def test_test_cases_accepts_stack_fields(self):
        properties = load("test-cases.schema.json")["properties"]["test_cases"]["items"]["properties"]
        for key in ("stack_id", "pack", "automation"):
            self.assertIn(key, properties)

    def test_e2e_cases_accepts_stack_fields(self):
        properties = load("e2e-cases.schema.json")["properties"]["e2e_cases"]["items"]["properties"]
        for key in ("stack_id", "pack", "automation"):
            self.assertIn(key, properties)

    def test_run_manifest_accepts_stack_and_report_fields(self):
        properties = load("run-manifest.schema.json")["properties"]["suites"]["items"]["properties"]
        for key in ("stack_id", "pack", "kind", "run_after", "coverage", "mutation"):
            self.assertIn(key, properties)
        self.assertEqual(properties["kind"]["enum"], ["test", "report"])
        self.assertIn("none", properties["coverage"]["properties"]["parser"]["enum"])
        self.assertIn("none", properties["mutation"]["properties"]["parser"]["enum"])

    @unittest.skipUnless(importlib.util.find_spec("jsonschema"), "jsonschema not installed")
    def test_example_cases_validate(self):
        import jsonschema  # type: ignore

        schema = load("test-cases.schema.json")
        data = json.loads((EXAMPLES / "python-service" / "test-cases.sample.json").read_text(encoding="utf-8"))
        jsonschema.validate(data, schema)


if __name__ == "__main__":
    unittest.main()
