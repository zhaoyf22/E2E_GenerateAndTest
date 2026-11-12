"""Compose stage prompts from the generic prompt and pack partials."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Optional

from .config import normalize_stacks
from .packs import Pack, get_pack


def compose_prompt(
    stage: str,
    stack_id: str,
    config: dict,
    packs: Mapping[str, Pack],
    prompts_dir: Path,
) -> str:
    prompts_dir = Path(prompts_dir).resolve()
    stage_name = stage if stage.endswith(".md") else f"{stage}.md"
    base_path = (prompts_dir / stage_name).resolve()
    try:
        base_path.relative_to(prompts_dir)
    except ValueError:
        raise ValueError(f"prompt stage escapes prompts directory: {stage}")
    if not base_path.is_file():
        raise FileNotFoundError(f"prompt not found: {base_path}")
    stacks = normalize_stacks(config, packs)
    stack = next((item for item in stacks if item.get("id") == stack_id), None)
    if stack is None:
        available = ", ".join(item.get("id", "") for item in stacks)
        raise KeyError(f"unknown stack: {stack_id} (available: {available})")
    pack = get_pack(dict(packs), stack.get("pack", ""))

    parts = [base_path.read_text(encoding="utf-8").rstrip()]
    for relative in pack.partials:
        partial = pack.path / relative
        if partial.is_file():
            parts.append(f"## Pack partial: {relative}\n\n{partial.read_text(encoding='utf-8').rstrip()}")

    commands = stack.get("commands") or {}
    stack_block = [
        "## Active stack",
        "",
        f"- stack_id: `{stack.get('id')}`",
        f"- pack: `{stack.get('pack')}`",
        f"- root: `{stack.get('root')}`",
    ]
    if commands:
        stack_block.append("- commands:")
        for key, value in commands.items():
            stack_block.append(f"  - `{key}`: `{value}`")
    parts.append("\n".join(stack_block))
    return "\n\n---\n\n".join(parts)
