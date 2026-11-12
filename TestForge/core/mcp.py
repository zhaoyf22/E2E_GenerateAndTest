"""Minimal stdio MCP server exposing TestForge CLI tools."""

from __future__ import annotations

import json
import sys
from typing import Any, Callable, Dict, List, Optional, TextIO, Tuple

VERSION = "0.1.0"
PROTOCOL_VERSION = "2024-11-05"

RunCli = Callable[[List[str]], Tuple[int, str, str]]

READ_TOOLS = {
    "testforge_pack",
    "testforge_validate",
    "testforge_matrix",
    "testforge_gate",
    "testforge_report",
}
WRITE_TOOLS = {
    "testforge_scaffold",
    "testforge_export",
    "testforge_run",
    "testforge_prompt",
}

TOOLS: List[Dict[str, Any]] = [
    {
        "name": "testforge_pack",
        "description": "Pack requirements, design, API, and code into a source-referenced context.",
        "inputSchema": {"type": "object", "properties": {"config": {"type": "string"}, "with_diff": {"type": "boolean"}}},
    },
    {
        "name": "testforge_validate",
        "description": "Validate testable-items, test-cases, or e2e-cases.",
        "inputSchema": {
            "type": "object",
            "required": ["cases"],
            "properties": {
                "cases": {"type": "string"},
                "kind": {"type": "string", "enum": ["auto", "testable", "test-cases", "e2e"]},
                "requirements": {"type": "string"},
                "schema": {"type": "string"},
                "stack": {"type": "string"},
            },
        },
    },
    {
        "name": "testforge_matrix",
        "description": "Build an AC coverage matrix, optionally grouped by stack.",
        "inputSchema": {
            "type": "object",
            "required": ["cases", "requirements"],
            "properties": {
                "cases": {"type": "string"},
                "requirements": {"type": "string"},
                "stack": {"type": "string"},
            },
        },
    },
    {
        "name": "testforge_gate",
        "description": "Evaluate quality gates from run results and reports.",
        "inputSchema": {
            "type": "object",
            "required": ["results"],
            "properties": {
                "results": {"type": "string"},
                "coverage": {"type": "string"},
                "mutation": {"type": "string"},
                "validation": {"type": "string"},
                "allow_missing_reports": {"type": "boolean"},
            },
        },
    },
    {
        "name": "testforge_report",
        "description": "Generate a Markdown report from run results.",
        "inputSchema": {
            "type": "object",
            "required": ["results"],
            "properties": {
                "results": {"type": "string"},
                "validation": {"type": "string"},
                "gate": {"type": "string"},
                "matrix": {"type": "string"},
            },
        },
    },
    {
        "name": "testforge_scaffold",
        "description": "Generate test skeletons from cases using a pack template.",
        "inputSchema": {
            "type": "object",
            "required": ["cases", "stack"],
            "properties": {
                "cases": {"type": "string"},
                "stack": {"type": "string"},
                "out": {"type": "string"},
                "force": {"type": "boolean"},
                "allow_write": {"type": "boolean"},
            },
        },
    },
    {
        "name": "testforge_export",
        "description": "Export cases to markdown/csv/gherkin/xlsx/json/testrail/xray.",
        "inputSchema": {
            "type": "object",
            "required": ["cases", "format"],
            "properties": {
                "cases": {"type": "string"},
                "format": {"type": "string"},
                "out": {"type": "string"},
                "stack": {"type": "string"},
                "allow_write": {"type": "boolean"},
            },
        },
    },
    {
        "name": "testforge_run",
        "description": "Run suites from a manifest.",
        "inputSchema": {
            "type": "object",
            "required": ["manifest"],
            "properties": {
                "manifest": {"type": "string"},
                "stack": {"type": "string"},
                "with_reports": {"type": "boolean"},
                "dry_run": {"type": "boolean"},
                "allow_write": {"type": "boolean"},
            },
        },
    },
    {
        "name": "testforge_prompt",
        "description": "Compose a stage prompt with pack prompt partials.",
        "inputSchema": {
            "type": "object",
            "required": ["stack", "stage"],
            "properties": {
                "stack": {"type": "string"},
                "stage": {"type": "string"},
                "out": {"type": "string"},
                "allow_write": {"type": "boolean"},
            },
        },
    },
]


def _cli_args(name: str, args: Dict[str, Any]) -> List[str]:
    if name == "testforge_pack":
        result = ["pack"]
        if args.get("config"):
            result += ["--config", str(args["config"])]
        if args.get("with_diff"):
            result.append("--with-diff")
        return result
    if name == "testforge_validate":
        result = ["validate", "--cases", str(args["cases"])]
        for key, flag in (("kind", "--kind"), ("requirements", "--requirements"), ("schema", "--schema"), ("stack", "--stack")):
            if args.get(key):
                result += [flag, str(args[key])]
        return result
    if name == "testforge_matrix":
        result = ["matrix", "--cases", str(args["cases"]), "--requirements", str(args["requirements"])]
        if args.get("stack"):
            result += ["--stack", str(args["stack"])]
        return result
    if name == "testforge_gate":
        result = ["gate", "--results", str(args["results"])]
        for key, flag in (("coverage", "--coverage"), ("mutation", "--mutation"), ("validation", "--validation")):
            if args.get(key):
                result += [flag, str(args[key])]
        if args.get("allow_missing_reports"):
            result.append("--allow-missing-reports")
        return result
    if name == "testforge_report":
        result = ["report", "--results", str(args["results"])]
        for key, flag in (("validation", "--validation"), ("gate", "--gate"), ("matrix", "--matrix")):
            if args.get(key):
                result += [flag, str(args[key])]
        return result
    if name == "testforge_scaffold":
        result = ["scaffold", "--cases", str(args["cases"]), "--stack", str(args["stack"])]
        if args.get("out"):
            result += ["--out", str(args["out"])]
        if args.get("force"):
            result.append("--force")
        return result
    if name == "testforge_export":
        result = ["export", "--cases", str(args["cases"]), "--format", str(args["format"])]
        if args.get("out"):
            result += ["--out", str(args["out"])]
        if args.get("stack"):
            result += ["--stack", str(args["stack"])]
        return result
    if name == "testforge_run":
        result = ["run", "--manifest", str(args["manifest"])]
        if args.get("stack"):
            result += ["--stack", str(args["stack"])]
        if args.get("with_reports"):
            result.append("--with-reports")
        if args.get("dry_run"):
            result.append("--dry-run")
        return result
    if name == "testforge_prompt":
        result = ["prompt", "--stack", str(args["stack"]), "--stage", str(args["stage"])]
        if args.get("out"):
            result += ["--out", str(args["out"])]
        return result
    raise ValueError(f"unknown tool: {name}")


def handle_request(
    request: Dict[str, Any],
    run_cli: RunCli,
    allow_write: bool = False,
) -> Optional[Dict[str, Any]]:
    request_id = request.get("id")
    if "id" not in request:
        return None
    method = request.get("method")
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "testforge", "version": VERSION},
            },
        }
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": TOOLS}}
    if method == "tools/call":
        params = request.get("params") or {}
        name = str(params.get("name") or "")
        args = params.get("arguments") or {}
        if name not in READ_TOOLS and name not in WRITE_TOOLS:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"content": [{"type": "text", "text": f"unknown tool: {name}"}], "isError": True},
            }
        if name in WRITE_TOOLS and not allow_write and not args.get("allow_write"):
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [{"type": "text", "text": "write permission required: start mcp with --allow-write or pass allow_write=true"}],
                    "isError": True,
                },
            }
        try:
            cli_args = _cli_args(name, args)
            code, stdout, stderr = run_cli(cli_args)
        except Exception as exc:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"content": [{"type": "text", "text": str(exc)}], "isError": True},
            }
        text = stdout or stderr or ""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {"content": [{"type": "text", "text": text}], "isError": code != 0},
        }
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": -32601, "message": f"method not found: {method}"},
    }


def serve(
    run_cli: RunCli,
    allow_write: bool = False,
    stdin: Optional[TextIO] = None,
    stdout: Optional[TextIO] = None,
) -> int:
    input_stream = stdin or sys.stdin
    output_stream = stdout or sys.stdout
    for line in input_stream:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except Exception:
            output_stream.write(json.dumps({
                "jsonrpc": "2.0", "id": None,
                "error": {"code": -32700, "message": "parse error"},
            }) + "\n")
            output_stream.flush()
            continue
        response = handle_request(request, run_cli, allow_write=allow_write)
        if response is not None:
            output_stream.write(json.dumps(response, ensure_ascii=False) + "\n")
            output_stream.flush()
    return 0
