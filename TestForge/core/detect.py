"""Detect project stacks from marker files and pack manifests."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple, Union

from .packs import Pack

IGNORED_DIRS = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "dist",
    "build",
    "__pycache__",
    ".testforge",
    ".mypy_cache",
    ".pytest_cache",
}

PACKAGE_MARKERS = (
    "package.json",
    "pyproject.toml",
    "requirements.txt",
    "setup.py",
    "setup.cfg",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    "CMakeLists.txt",
    "meson.build",
    "BUILD.bazel",
    "Chart.yaml",
    "kustomization.yaml",
)


@dataclass(frozen=True)
class DetectedStack:
    id: str
    pack: str
    root: str
    confidence: int


def _is_ignored(path: Path) -> bool:
    return any(part in IGNORED_DIRS for part in path.parts)


def _iter_matches(project_root: Path, pattern: str, max_depth: int = 8) -> List[Path]:
    try:
        if any(ch in pattern for ch in "*?["):
            candidates = project_root.glob(pattern)
        else:
            candidates = project_root.rglob(pattern)
    except Exception:
        return []
    matches: List[Path] = []
    for candidate in candidates:
        if not candidate.is_file() or _is_ignored(candidate):
            continue
        try:
            relative = candidate.relative_to(project_root)
        except ValueError:
            continue
        # Depth of the containing directory relative to the project root.
        if len(relative.parts) - 1 > max_depth:
            continue
        matches.append(candidate)
    return matches


def _nearest_package_dir(path: Path, project_root: Path) -> Path:
    current = path.parent
    while True:
        if any((current / marker).is_file() for marker in PACKAGE_MARKERS):
            return current
        if current == project_root or current.parent == current:
            return project_root
        current = current.parent


def _slug(text: str) -> str:
    text = re.sub(r"[^\w一-鿿\-]+", "-", text).strip("-").lower()
    return text or "stack"


def _unique_id(base: str, used: set) -> str:
    candidate = base
    index = 2
    while candidate in used:
        candidate = f"{base}-{index}"
        index += 1
    used.add(candidate)
    return candidate


def detect_stacks(
    project_root: Union[Path, str],
    packs: Mapping[str, Pack],
    max_depth: int = 8,
) -> List[DetectedStack]:
    project_root = Path(project_root).resolve()
    found: Dict[Tuple[str, str], Tuple[Path, int, int]] = {}

    for pack in sorted(packs.values(), key=lambda item: item.id):
        detect = pack.manifest.get("detect") or {}
        files = [str(item) for item in (detect.get("files") or [])]
        globs = [str(item) for item in (detect.get("globs") or [])]
        priority = int(detect.get("priority") or 0)

        for marker in files:
            for path in _iter_matches(project_root, marker, max_depth):
                if path.name in PACKAGE_MARKERS:
                    root = path.parent
                else:
                    root = _nearest_package_dir(path, project_root)
                key = (pack.id, root.as_posix())
                previous = found.get(key)
                if previous is None or previous[1] < 2:
                    found[key] = (root, 2, priority)

        for pattern in globs:
            for path in _iter_matches(project_root, pattern, max_depth):
                root = _nearest_package_dir(path, project_root)
                key = (pack.id, root.as_posix())
                previous = found.get(key)
                if previous is None:
                    found[key] = (root, 1, priority)

    used_ids: set = set()
    stacks: List[DetectedStack] = []
    for (pack_id, root_text), (_root, confidence, priority) in sorted(
        found.items(),
        key=lambda item: (item[1][0].as_posix().count("/"), -item[1][1], -item[1][2], item[0][0], item[0][1]),
    ):
        root = Path(root_text)
        try:
            relative = root.relative_to(project_root).as_posix()
        except ValueError:
            relative = root.as_posix()
        if relative == ".":
            base_id = pack_id
        else:
            base_id = f"{pack_id}-{_slug(relative.replace('/', '-'))}"
        stack_id = _unique_id(base_id, used_ids)
        stacks.append(DetectedStack(id=stack_id, pack=pack_id, root=relative, confidence=confidence))
    return stacks
