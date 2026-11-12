"""TestRail and Xray CSV export formats."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict, Sequence

TESTRAIL_HEADER = [
    "ID", "Title", "Section", "Type", "Priority",
    "Preconditions", "Steps", "Expected", "References",
]
XRAY_HEADER = [
    "Issue Key", "Summary", "Description", "Test Type",
    "Steps", "Expected Result", "Labels", "Requirement",
]


def _steps_text(case: Dict[str, Any]) -> str:
    raw = case.get("steps")
    lines = []
    if isinstance(raw, list):
        for index, item in enumerate(raw, 1):
            if isinstance(item, dict):
                action = str(item.get("action", ""))
                expected = str(item.get("expected", ""))
            else:
                action, expected = str(item), ""
            lines.append(f"{index}. {action}")
            if expected:
                lines.append(f"   预期: {expected}")
    return "\n".join(lines)


def _join(value: Any) -> str:
    if isinstance(value, list):
        return "; ".join(str(item) for item in value)
    if value is None:
        return ""
    return str(value)


def _section(case: Dict[str, Any]) -> str:
    stack = str(case.get("stack_id") or "default")
    feature = str(case.get("feature") or "Generated")
    return f"{stack}/{feature}"


def export_testrail_csv(cases: Sequence[Dict[str, Any]], out: Path) -> Path:
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(TESTRAIL_HEADER)
        for case in cases:
            writer.writerow([
                case.get("id", ""),
                case.get("title", ""),
                _section(case),
                case.get("type", ""),
                case.get("priority", ""),
                _join(case.get("preconditions")),
                _steps_text(case),
                case.get("expected_result", ""),
                _join(case.get("source_refs")),
            ])
    return out


def export_xray_csv(cases: Sequence[Dict[str, Any]], out: Path) -> Path:
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(XRAY_HEADER)
        for case in cases:
            writer.writerow([
                case.get("id", ""),
                case.get("title", ""),
                case.get("expected_result", ""),
                case.get("type", "") or "Manual",
                _steps_text(case),
                case.get("expected_result", ""),
                _join(case.get("tags")),
                _join(case.get("ac_ids")),
            ])
    return out
