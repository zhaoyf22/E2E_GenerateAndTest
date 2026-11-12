"""Deterministic test skeleton generation from test cases."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Sequence

from .config import slugify
from .packs import Pack


def _steps(case: Dict[str, Any]) -> List[Dict[str, str]]:
    raw = case.get("steps")
    if isinstance(raw, list) and raw:
        result = []
        for item in raw:
            if isinstance(item, dict):
                result.append({"action": str(item.get("action", "")), "expected": str(item.get("expected", ""))})
            else:
                result.append({"action": str(item), "expected": ""})
        return result
    result = []
    for key in ("given", "when", "then"):
        value = case.get(key)
        if isinstance(value, str) and value.strip():
            result.append({"action": f"{key.upper()}: {value.strip()}", "expected": ""})
    return result


def _steps_text(case: Dict[str, Any]) -> str:
    lines = []
    for index, step in enumerate(_steps(case), 1):
        lines.append(f"{index}. {step['action']}")
        if step.get("expected"):
            lines.append(f"   预期: {step['expected']}")
    return "\n".join(lines)


def _render(template: str, case: Dict[str, Any], stack_id: str) -> str:
    module = slugify(str(case.get("id") or case.get("title") or "case")).replace("-", "_").lower()
    replacements = {
        "${id}": str(case.get("id", "")),
        "${title}": str(case.get("title", "")),
        "${feature}": str(case.get("feature", "")),
        "${steps}": _steps_text(case),
        "${expected}": str(case.get("expected_result", "")),
        "${stack}": stack_id,
        "${module}": module,
    }
    for key, value in replacements.items():
        template = template.replace(key, value)
    return template


def scaffold_cases(
    cases: Sequence[Dict[str, Any]],
    pack: Pack,
    stack_id: str,
    out_dir: Path,
    force: bool = False,
) -> Dict[str, Any]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    scaffold = pack.scaffold or {}
    default_template = str(scaffold.get("default_template") or "")
    by_type = scaffold.get("by_type") if isinstance(scaffold.get("by_type"), dict) else {}

    written: List[Dict[str, Any]] = []
    skipped: List[Dict[str, Any]] = []
    for case in cases:
        if not isinstance(case, dict):
            continue
        template_id = str(by_type.get(case.get("type") or "e2e") or default_template).strip()
        template = next((item for item in pack.templates if str(item.get("id")) == template_id), None)
        if not template:
            skipped.append({"case_id": case.get("id"), "reason": f"no template for {template_id or '<none>'}"})
            continue
        source = pack.path / str(template.get("path") or "")
        if not source.is_file():
            skipped.append({"case_id": case.get("id"), "reason": f"template file not found: {source}"})
            continue
        content = _render(source.read_text(encoding="utf-8"), case, stack_id)
        target_text = str(template.get("target") or "")
        if target_text:
            target_rel = _render(target_text, case, stack_id)
        else:
            suffix = source.suffix or ".txt"
            target_rel = f"{slugify(str(case.get('id') or case.get('title') or 'case'))}{suffix}"
        target = (out_dir / target_rel).resolve()
        try:
            target.relative_to(out_dir.resolve())
        except ValueError:
            skipped.append({"case_id": case.get("id"), "reason": f"target escapes out_dir: {target_rel}"})
            continue
        if target.exists() and not force:
            skipped.append({"case_id": case.get("id"), "reason": f"exists: {target}"})
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        written.append({"case_id": case.get("id"), "template": template_id, "file": str(target)})

    manifest = {
        "pack": pack.id,
        "stack_id": stack_id,
        "out_dir": str(out_dir),
        "written": written,
        "skipped": skipped,
    }
    (out_dir / "scaffold-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return manifest
