import unittest

from core.mcp import handle_request


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


if __name__ == "__main__":
    unittest.main()
