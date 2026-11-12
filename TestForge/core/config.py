"""Configuration loading, normalization, and stack composition."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

DEFAULT_CONFIG_NAME = "testforge.config.json"

DEFAULT_CONFIG: Dict[str, Any] = {
    "project": {"name": "my-project", "type": "platform", "root": "."},
    "inputs": {
        "docs": [
            "docs/**/*.md",
            "requirements/**/*.md",
            "requirements/**/*.txt",
            "PRD.md",
            "REQUIREMENTS.md",
            "requirements.md",
        ],
        "api": [
            "openapi.yaml",
            "openapi.yml",
            "openapi.json",
            "openapi/**/*.yaml",
            "openapi/**/*.yml",
            "openapi/**/*.json",
            "api/**/*.yaml",
        ],
        "code": ["src/**/*.py"],
        "tests": ["tests/**/*.py"],
        "ignore": [
            "**/node_modules/**",
            "**/.venv/**",
            "**/venv/**",
            "**/dist/**",
            "**/build/**",
            "**/.git/**",
            "**/__pycache__/**",
            "**/.testforge/**",
        ],
    },
    "stack": {},
    "commands": {
        "unit": "pytest -q",
        "api": "pytest tests/api -q",
        "e2e": "npx playwright test",
    },
    "quality_gates": {
        "ac_coverage_min": 0.9,
        "duplicate_similarity_max": 0.85,
        "line_coverage_min": 0.0,
        "line_coverage_delta_min": 0.0,
        "mutation_score_min": 0.0,
        "flaky_rate_max": 0.02,
        "cases_min": 0,
    },
    "generation": {
        "language": "zh-CN",
        "max_cases_per_ac": 12,
        "max_context_chars_per_entry": 12000,
        "techniques": ["EP", "BVA", "DT", "ST", "scenario", "error-guessing", "permission"],
        "default_priority": "P1",
    },
    "adapters": {},
    "paths": {
        "context": ".testforge/context",
        "cases": ".testforge/cases",
        "runs": ".testforge/runs",
        "reports": ".testforge/reports",
        "coverage_report": "",
        "mutation_report": "",
        "validation_report": ".testforge/reports/validation-report.json",
    },
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def normalize_config_path(path: str) -> Path:
    p = Path(path)
    if p.is_dir():
        p = p / DEFAULT_CONFIG_NAME
    return p


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = deep_merge(out[key], value)
        else:
            out[key] = value
    return out


def as_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def load_config(path: str) -> Dict[str, Any]:
    p = normalize_config_path(path)
    if not p.exists():
        raise SystemExit(f"Config not found: {p}")
    try:
        data = read_json(p)
    except Exception as exc:
        raise SystemExit(f"Invalid config JSON: {p}: {exc}")
    if not isinstance(data, dict):
        raise SystemExit(f"Config must be a JSON object: {p}")
    return deep_merge(DEFAULT_CONFIG, data)


def project_root(config: Dict[str, Any], config_path: str) -> Path:
    base = normalize_config_path(config_path).resolve().parent
    root = Path(as_dict(config.get("project")).get("root") or ".")
    if not root.is_absolute():
        root = (base / root).resolve()
    return root


def rel_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _pack_attr(pack: Any, name: str) -> Dict[str, Any]:
    value = getattr(pack, name, None)
    if callable(value):
        value = value()
    return value if isinstance(value, dict) else {}


def _merge_mapping(base: Mapping[str, Any], override: Mapping[str, Any]) -> Dict[str, Any]:
    out = dict(base or {})
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _merge_mapping(out[key], value)
        else:
            out[key] = value
    return out


def _synthesize_pack_id(project_type: str, packs: Mapping[str, Any]) -> str:
    def has(pack_id: str) -> bool:
        return pack_id in packs

    project_type = (project_type or "").lower()
    if project_type == "frontend":
        return "frontend-web"
    if project_type == "cli":
        return "cpp-cli" if has("cpp-cli") else "python-service"
    if project_type in ("service", "backend"):
        return "python-service" if (not packs or has("python-service")) else "java-service"
    if project_type == "platform":
        return "python-service" if (not packs or has("python-service")) else "java-service"
    return "python-service"


def normalize_stacks(
    config: Dict[str, Any],
    packs: Optional[Mapping[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Return a deterministic list of stack dicts.

    Explicit config["stacks"] wins. Without it, synthesize one stack so old
    single-profile configs keep working.
    """
    packs = packs or {}
    raw_stacks = config.get("stacks")
    if isinstance(raw_stacks, list) and raw_stacks:
        result: List[Dict[str, Any]] = []
        seen: set = set()
        for index, raw in enumerate(raw_stacks):
            if not isinstance(raw, dict):
                raise ValueError(f"stacks[{index}] must be an object")
            stack_id = str(raw.get("id") or "").strip()
            if not stack_id:
                raise ValueError(f"stacks[{index}] is missing id")
            if stack_id in seen:
                raise ValueError(f"duplicate stack id: {stack_id}")
            seen.add(stack_id)
            pack_id = str(raw.get("pack") or "").strip()
            if not pack_id:
                raise ValueError(f"stack {stack_id} is missing pack")
            pack = packs.get(pack_id) if packs else None
            if packs and pack is None:
                raise ValueError(f"stack {stack_id} references unknown pack: {pack_id}")
            commands = _merge_mapping(_pack_attr(pack, "commands"), as_dict(raw.get("commands")))
            inputs = _merge_mapping(_pack_attr(pack, "inputs"), as_dict(raw.get("inputs")))
            coverage = _merge_mapping(_pack_attr(pack, "coverage"), as_dict(raw.get("coverage")))
            mutation = _merge_mapping(_pack_attr(pack, "mutation"), as_dict(raw.get("mutation")))
            result.append({
                "id": stack_id,
                "pack": pack_id,
                "root": str(raw.get("root") or "."),
                "kind": str(raw.get("kind") or "language"),
                "commands": commands,
                "inputs": inputs,
                "coverage": coverage,
                "mutation": mutation,
                "quality_gates": _merge_mapping(as_dict(config.get("quality_gates")), as_dict(raw.get("quality_gates"))),
                "tags": as_list(raw.get("tags")),
            })
        return result

    project_type = str(as_dict(config.get("project")).get("type") or "platform")
    pack_id = _synthesize_pack_id(project_type, packs)
    pack = packs.get(pack_id) if packs else None
    stack = {
        "id": "default",
        "pack": pack_id,
        "root": ".",
        "kind": "language",
        "commands": _merge_mapping(_pack_attr(pack, "commands"), as_dict(config.get("commands"))),
        "inputs": _merge_mapping(_pack_attr(pack, "inputs"), as_dict(config.get("inputs"))),
        "coverage": _merge_mapping(_pack_attr(pack, "coverage"), as_dict(config.get("coverage"))),
        "mutation": _merge_mapping(_pack_attr(pack, "mutation"), as_dict(config.get("mutation"))),
        "quality_gates": as_dict(config.get("quality_gates")),
        "tags": [],
    }
    return [stack]


def stack_root(config: Dict[str, Any], stack: Dict[str, Any], config_path: str) -> Path:
    root = Path(stack.get("root") or ".")
    base = project_root(config, config_path)
    if not root.is_absolute():
        root = base / root
    return root.resolve()


def slugify(text: str) -> str:
    text = re.sub(r"[^\w一-鿿\- ]+", "", text or "", flags=re.UNICODE)
    text = re.sub(r"\s+", "-", text.strip())
    return text[:80] or "stack"
