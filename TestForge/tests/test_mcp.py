import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from core.mcp import handle_request, serve

SUITE = Path(__file__).resolve().parents[1]


def fake_cli(args):
    return 0, "ok " + " ".join(args), ""


class McpTest(unittest.TestCase):
    def test_initialize_and_tools_list(self):
        response = handle_request({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}, fake_cli)
        self.assertEqual(response["result"]["serverInfo"]["name"], "testforge")
        response = handle_request({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}, fake_cli)
        names = {tool["name"] for tool in response["result"]["tools"]}
        self.assertTrue({"testforge_validate", "testforge_matrix", "testforge_gate", "testforge_report"}.issubset(names))

    def test_validate_tool_maps_to_cli(self):
        response = handle_request({
            "jsonrpc": "2.0", "id": 3, "method": "tools/call",
            "params": {"name": "testforge_validate", "arguments": {"cases": "cases.json", "kind": "test-cases"}},
        }, fake_cli)
        self.assertFalse(response["result"]["isError"])
        self.assertIn("validate --cases cases.json --kind test-cases", response["result"]["content"][0]["text"])

    def test_write_tool_requires_permission(self):
        response = handle_request({
            "jsonrpc": "2.0", "id": 4, "method": "tools/call",
            "params": {"name": "testforge_run", "arguments": {"manifest": "m.json"}},
        }, fake_cli)
        self.assertTrue(response["result"]["isError"])
        self.assertIn("write permission required", response["result"]["content"][0]["text"])

    def test_write_tool_with_permission(self):
        response = handle_request({
            "jsonrpc": "2.0", "id": 5, "method": "tools/call",
            "params": {"name": "testforge_run", "arguments": {"manifest": "m.json", "allow_write": True}},
        }, fake_cli)
        self.assertFalse(response["result"]["isError"])

    def test_non_object_json_returns_invalid_request(self):
        stdout = io.StringIO()
        serve(fake_cli, stdin=io.StringIO("1\n"), stdout=stdout)
        response = json.loads(stdout.getvalue().strip())
        self.assertEqual(response["error"]["code"], -32600)

    def test_non_object_request_direct(self):
        response = handle_request([1, 2, 3], fake_cli)  # type: ignore[arg-type]
        self.assertEqual(response["error"]["code"], -32600)

    def test_allow_write_env_var_enables_write_tools(self):
        request = json.dumps({
            "jsonrpc": "2.0", "id": 6, "method": "tools/call",
            "params": {"name": "testforge_scaffold", "arguments": {"cases": "nope.json", "stack": "api"}},
        }) + "\n"
        with tempfile.TemporaryDirectory() as tmp:
            base_env = dict(os.environ)
            base_env.pop("TESTFORGE_MCP_ALLOW_WRITE", None)

            def call(env):
                return subprocess.run(
                    [sys.executable, str(SUITE / "testforge.py"), "mcp"],
                    input=request, cwd=tmp, env=env, capture_output=True,
                    text=True, encoding="utf-8", timeout=120,
                )

            denied = call(base_env)
            denied_text = json.loads(denied.stdout.strip().splitlines()[0])["result"]["content"][0]["text"]
            self.assertIn("write permission required", denied_text)

            allowed_env = dict(base_env)
            allowed_env["TESTFORGE_MCP_ALLOW_WRITE"] = "1"
            allowed = call(allowed_env)
            allowed_text = json.loads(allowed.stdout.strip().splitlines()[0])["result"]["content"][0]["text"]
            self.assertNotIn("write permission required", allowed_text)


if __name__ == "__main__":
    unittest.main()
