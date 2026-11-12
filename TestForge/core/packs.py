"""Pack manifest loading and validation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class Pack:
    id: str
    path: Path
    manifest: Dict[str, Any]

    @property
    def display_name(self) -> str:
        return str(self.manifest.get("display_name") or self.id)

    @property
    def commands(self) -> Dict[str, str]:
        return dict(self.manifest.get("commands") or {})

    @property
    def inputs(self) -> Dict[str, List[str]]:
        raw = self.manifest.get("inputs") or {}
        return {str(k): list(v) for k, v in raw.items() if isinstance(v, list)}

    @property
    def tools(self) -> List[Dict[str, Any]]:
        raw = self.manifest.get("tools") or []
        return [dict(item) for item in raw if isinstance(item, dict)]

    @property
    def templates(self) -> List[Dict[str, Any]]:
        raw = self.manifest.get("templates") or []
        return [dict(item) for item in raw if isinstance(item, dict)]

    @property
    def scaffold(self) -> Dict[str, Any]:
        raw = self.manifest.get("scaffold")
        return dict(raw) if isinstance(raw, dict) else {}

    @property
    def coverage(self) -> Dict[str, Any]:
        raw = self.manifest.get("coverage")
        return dict(raw) if isinstance(raw, dict) else {}

    @property
    def mutation(self) -> Dict[str, Any]:
        raw = self.manifest.get("mutation")
        return dict(raw) if isinstance(raw, dict) else {}

    @property
    def partials(self) -> List[str]:
        raw = self.manifest.get("prompt_partials") or []
        return [str(item) for item in raw]

    @property
    def adapters(self) -> List[str]:
        raw = self.manifest.get("adapters") or []
        return [str(item) for item in raw]

    @property
    def ci(self) -> List[str]:
        raw = self.manifest.get("ci") or []
        return [str(item) for item in raw]

    @property
    def acceptance(self) -> str:
        return str(self.manifest.get("acceptance") or "")


def load_pack(pack_dir: Path) -> Pack:
    manifest_path = Path(pack_dir) / "pack.json"
    if not manifest_path.is_file():
        raise ValueError(f"pack.json not found: {manifest_path}")
    data = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError(f"pack.json must be an object: {manifest_path}")
    pack_id = str(data.get("id") or "").strip()
    if not pack_id:
        raise ValueError(f"pack.json is missing id: {manifest_path}")
    errors = validate_pack(data)
    if errors:
        raise ValueError(f"invalid pack.json {manifest_path}: {'; '.join(errors)}")
    return Pack(id=pack_id, path=Path(pack_dir), manifest=data)


def load_packs(root: Path) -> Dict[str, Pack]:
    root = Path(root)
    packs: Dict[str, Pack] = {}
    if not root.is_dir():
        return packs
    for child in sorted(root.iterdir(), key=lambda p: p.name):
        if not child.is_dir():
            continue
        manifest = child / "pack.json"
        if not manifest.is_file():
            continue
        pack = load_pack(child)
        if pack.id in packs:
            raise ValueError(f"duplicate pack id: {pack.id}")
        packs[pack.id] = pack
    return packs


def get_pack(packs: Dict[str, Pack], pack_id: str) -> Pack:
    if pack_id not in packs:
        available = ", ".join(sorted(packs)) or "<none>"
        raise KeyError(f"unknown pack: {pack_id} (available: {available})")
    return packs[pack_id]


def validate_pack(manifest: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    if not isinstance(manifest, dict):
        return ["pack manifest must be an object"]
    if not manifest.get("id"):
        errors.append("missing id")
    commands = manifest.get("commands")
    if commands is not None and not isinstance(commands, dict):
        errors.append("commands must be an object")
    inputs = manifest.get("inputs")
    if inputs is not None and not isinstance(inputs, dict):
        errors.append("inputs must be an object")
    tools = manifest.get("tools")
    if tools is not None and not isinstance(tools, list):
        errors.append("tools must be a list")
    templates = manifest.get("templates")
    if templates is not None and not isinstance(templates, list):
        errors.append("templates must be a list")
    scaffold = manifest.get("scaffold")
    if scaffold is not None and not isinstance(scaffold, dict):
        errors.append("scaffold must be an object")
    coverage = manifest.get("coverage")
    if coverage is not None and not isinstance(coverage, dict):
        errors.append("coverage must be an object")
    mutation = manifest.get("mutation")
    if mutation is not None and not isinstance(mutation, dict):
        errors.append("mutation must be an object")
    return errors
