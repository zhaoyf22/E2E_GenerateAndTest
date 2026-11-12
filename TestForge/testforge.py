#!/usr/bin/env python3
"""TestForge CLI: pack context, validate cases, export, run suites, gate, report.

Designed to be dependency-free (Python 3.8+ stdlib). Optional integrations:
  - docling / pypdf / python-docx for PDF/DOCX extraction
  - openpyxl for XLSX export
"""

from __future__ import annotations

import argparse
import csv
import difflib
import fnmatch
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from core.config import normalize_stacks
from core.detect import detect_stacks
from core.packs import load_packs

SUITE_ROOT = Path(__file__).resolve().parent
VERSION = "0.1.0"
DEFAULT_CONFIG_NAME = "testforge.config.json"

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


DEFAULT_CONFIG: Dict[str, Any] = {
    "project": {"name": "my-project", "type": "platform", "root": "."},
    "inputs": {
        "docs": ["docs/**/*.md", "requirements/**/*.md", "requirements/**/*.txt", "PRD.md", "REQUIREMENTS.md", "requirements.md"],
        "api": ["openapi.yaml", "openapi.yml", "openapi.json", "openapi/**/*.yaml", "openapi/**/*.yml", "openapi/**/*.json", "api/**/*.yaml"],
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

ID_PREFIX = {"docs": "DOC", "api": "API", "code": "CODE", "tests": "TEST", "diff": "DIFF"}

TEXT_EXTS = {
    ".md", ".markdown", ".txt", ".rst", ".adoc",
    ".yaml", ".yml", ".json", ".toml", ".ini", ".cfg",
    ".py", ".ts", ".tsx", ".js", ".jsx", ".java", ".kt",
    ".go", ".rs", ".cs", ".rb", ".php", ".swift", ".scala",
    ".sql", ".feature", ".xml", ".html", ".css", ".vue", ".svelte",
}

LANG_BY_EXT = {
    ".py": "python", ".ts": "typescript", ".tsx": "tsx", ".js": "javascript",
    ".jsx": "jsx", ".java": "java", ".kt": "kotlin", ".go": "go", ".rs": "rust",
    ".cs": "csharp", ".rb": "ruby", ".php": "php", ".sql": "sql",
    ".feature": "gherkin", ".xml": "xml", ".html": "html", ".css": "css",
    ".yaml": "yaml", ".yml": "yaml", ".json": "json", ".md": "markdown",
}

VAGUE_PATTERNS = [
    r"输入(一些|相关|必要)?信息",
    r"验证(功能|结果)?(正常|正确|成功)",
    r"正常(显示|运行|工作)",
    r"符合预期",
    r"适当",
    r"合理",
    r"等等",
    r"enter (some )?(data|information)",
    r"verify (it )?works",
    r"as expected",
    r"should work",
    r"correctly",
]

TECHNIQUES = {
    "EP", "BVA", "DT", "ST", "scenario", "error-guessing", "permission",
    "idempotency", "concurrency", "contract", "property", "pairwise",
}
PRIORITIES = {"P0", "P1", "P2", "P3"}
CASE_TYPES = {
    "functional", "negative", "boundary", "permission", "state", "integration",
    "contract", "nonfunctional", "e2e", "regression",
}
CATEGORIES = {
    "functional", "negative", "boundary", "permission", "state", "integration",
    "contract", "nonfunctional", "e2e",
}


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def read_optional_json(path: Optional[str]) -> Any:
    if not path:
        return {}
    p = Path(path)
    if not p.is_file():
        return {}
    try:
        return read_json(p)
    except Exception:
        return {}


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = deep_merge(out[key], value)
        else:
            out[key] = value
    return out


def normalize_config_path(path: str) -> Path:
    p = Path(path)
    if p.is_dir():
        p = p / DEFAULT_CONFIG_NAME
    return p


def load_config(path: str) -> Dict[str, Any]:
    p = normalize_config_path(path)
    if not p.exists():
        raise SystemExit(f"Config not found: {p}")
    try:
        data = read_json(p)
    except Exception as exc:
        raise SystemExit(f"Invalid config JSON: {p}: {exc}")
    return deep_merge(DEFAULT_CONFIG, data)


def config_root(config: Dict[str, Any], config_path: str) -> Path:
    base = Path(config_path).resolve().parent
    root = Path(config.get("project", {}).get("root", "."))
    if not root.is_absolute():
        root = (base / root).resolve()
    return root


def rel_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def slugify(text: str) -> str:
    text = re.sub(r"[^\w一-鿿\- ]+", "", text, flags=re.UNICODE)
    text = re.sub(r"\s+", "-", text.strip())
    return text[:80] or "section"


def truncate(text: str, limit: int) -> Tuple[str, bool]:
    if limit <= 0 or len(text) <= limit:
        return text, False
    return text[:limit], True


def as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def as_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def module_available(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except Exception:
        return False


def is_ignored(rel: str, ignores: Sequence[str]) -> bool:
    rel = rel.replace("\\", "/")
    for pat in ignores:
        pat = (pat or "").replace("\\", "/")
        if not pat:
            continue
        if fnmatch.fnmatch(rel, pat):
            return True
        prefix = pat.rstrip("/*")
        if prefix and (rel == prefix or rel.startswith(prefix.rstrip("/") + "/")):
            return True
    return False


def expand_files(root: Path, patterns: Sequence[str], ignores: Sequence[str]) -> List[Path]:
    found: Dict[str, Path] = {}
    for pat in patterns:
        if not pat:
            continue
        p = Path(pat)
        try:
            if p.is_absolute():
                candidates = [p] if p.is_file() else list(p.rglob("*"))
            else:
                candidates = list(root.glob(pat))
        except Exception:
            continue
        for candidate in candidates:
            if not candidate.is_file():
                continue
            rel = rel_path(candidate, root)
            if is_ignored(rel, ignores):
                continue
            found[str(candidate.resolve())] = candidate
    return sorted(found.values(), key=lambda x: x.as_posix())


def extract_text(path: Path) -> Tuple[Optional[str], str]:
    suffix = path.suffix.lower()
    if suffix in TEXT_EXTS:
        try:
            return path.read_text(encoding="utf-8-sig", errors="replace"), "text"
        except Exception as exc:
            return None, f"read-error: {exc}"
    if suffix in (".pdf", ".pptx", ".xlsx", ".png", ".jpg", ".jpeg", ".tiff", ".tif"):
        try:
            from docling.document_converter import DocumentConverter  # type: ignore
            doc = DocumentConverter().convert(str(path)).document
            return doc.export_to_markdown(), "docling"
        except Exception:
            pass
        if suffix == ".pdf":
            try:
                import pypdf  # type: ignore
                reader = pypdf.PdfReader(str(path))
                return "\n".join((page.extract_text() or "") for page in reader.pages), "pypdf"
            except Exception:
                return None, "pdf-unsupported (install docling or pypdf)"
        return None, f"{suffix[1:]}-unsupported (install docling)"
    if suffix == ".docx":
        try:
            import docx  # type: ignore
            document = docx.Document(str(path))
            parts = [p.text for p in document.paragraphs]
            for table in document.tables:
                for row in table.rows:
                    parts.append(" | ".join(cell.text for cell in row.cells))
            return "\n".join(parts), "python-docx"
        except Exception:
            return None, "docx-unsupported (install python-docx)"
    return None, "binary"


HEADING_LINE_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


def split_markdown(text: str) -> List[Tuple[str, str]]:
    """Split Markdown by headings, ignoring headings inside fenced code blocks."""
    sections: List[Tuple[str, str]] = []
    current_title = ""
    current_lines: List[str] = []
    in_fence = False
    fence_marker = ""

    def flush() -> None:
        body = "\n".join(current_lines).strip()
        if current_title or body:
            sections.append((current_title, body))

    for raw_line in text.splitlines():
        stripped = raw_line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            marker = stripped[:3]
            if not in_fence:
                in_fence = True
                fence_marker = marker
            elif marker == fence_marker:
                in_fence = False
                fence_marker = ""
            current_lines.append(raw_line)
            continue
        if not in_fence:
            match = HEADING_LINE_RE.match(raw_line.strip())
            if match:
                flush()
                current_title = match.group(2).strip()
                current_lines = []
                continue
        current_lines.append(raw_line)
    flush()
    return sections


def fence_for(text: str) -> str:
    """Return a code fence longer than any backtick run in the content."""
    longest = 0
    for match in re.finditer(r"`+", text or ""):
        longest = max(longest, len(match.group(0)))
    return "`" * max(3, longest + 1)


# ---------------------------------------------------------------------------
# init
# ---------------------------------------------------------------------------

def _split_values(values: Optional[Sequence[str]]) -> List[str]:
    result: List[str] = []
    for value in values or []:
        for part in str(value).split(","):
            part = part.strip()
            if part:
                result.append(part)
    return result


def _unique_stack_id(base: str, used: set) -> str:
    candidate = base or "stack"
    index = 2
    while candidate in used:
        candidate = f"{base}-{index}"
        index += 1
    used.add(candidate)
    return candidate


def _stack_from_spec(spec: str, kind: str, used: set) -> Dict[str, Any]:
    pack, _, root = spec.partition(":")
    pack = pack.strip()
    root = root.strip() or "."
    if not pack:
        raise SystemExit(f"Invalid --{kind} spec: {spec!r}")
    base = pack if root == "." else f"{pack}-{slugify(root)}"
    return {"id": _unique_stack_id(base, used), "pack": pack, "root": root, "kind": kind}


def _load_new_profile(name: Optional[str]) -> Optional[Dict[str, Any]]:
    if not name:
        return None
    path = SUITE_ROOT / "profiles" / f"{name}.json"
    return read_json(path) if path.is_file() else None


def _load_old_profile(name: Optional[str]) -> Optional[Dict[str, Any]]:
    if not name:
        return None
    path = SUITE_ROOT / "config" / "profiles" / f"{name}.json"
    return read_json(path) if path.is_file() else None


def _build_run_manifest(config: Dict[str, Any], packs: Dict[str, Any], target: Path) -> Dict[str, Any]:
    stacks = normalize_stacks(config, packs)
    manifest = {"meta": {"project": target.name, "generated_at": now_iso()}, "suites": []}
    manifest_dir = (target / ".testforge").resolve()
    project_base = (target / (as_dict(config.get("project")).get("root") or ".")).resolve()
    for stack in stacks:
        stack_dir = (project_base / (stack.get("root") or ".")).resolve()
        cwd = os.path.relpath(str(stack_dir), str(manifest_dir)).replace("\\", "/")
        commands = stack.get("commands") or {}
        for key, command in commands.items():
            if key in ("unit", "integration", "api", "e2e", "orchestrate", "chaos", "cli-smoke"):
                kind, run_after = "test", []
            elif key in ("coverage", "mutation"):
                kind = "report"
                run_after = [
                    f"{stack.get('id')}-{dep}"
                    for dep in ("unit", "integration")
                    if dep in commands
                ]
            else:
                continue
            timeout = 1800 if key in ("e2e", "orchestrate", "chaos") else 600
            manifest["suites"].append({
                "name": f"{stack.get('id')}-{key}",
                "command": command,
                "cwd": cwd,
                "timeout": timeout,
                "kind": kind,
                "stack_id": stack.get("id"),
                "pack": stack.get("pack"),
                "run_after": run_after,
            })
    return manifest


def cmd_init(args: argparse.Namespace) -> int:
    packs = load_packs(SUITE_ROOT / "packs")
    if args.list_packs:
        for pack in sorted(packs.values(), key=lambda item: item.id):
            print(f"{pack.id:16} {pack.display_name}")
        return 0

    if not args.target:
        print("--target is required unless --list-packs is used.")
        return 2
    target = Path(args.target).resolve()
    if target == SUITE_ROOT:
        print("Target is the suite root; nothing to copy. Use --target <your-project>.")
        return 0

    profile_name = args.profile
    if profile_name is None and not args.detect and not args.stack and not args.surface:
        profile_name = "platform"
    new_profile = _load_new_profile(profile_name)
    old_profile = _load_old_profile(profile_name)

    used_ids: set = set()
    stacks: List[Dict[str, Any]] = []
    surfaces: List[Dict[str, Any]] = []
    if new_profile:
        for raw in new_profile.get("stacks") or []:
            item = dict(raw)
            item["kind"] = item.get("kind", "language")
            item["id"] = _unique_stack_id(str(item.get("id") or item.get("pack")), used_ids)
            stacks.append(item)
        for raw in new_profile.get("surfaces") or []:
            item = dict(raw)
            item["kind"] = "surface"
            item["id"] = _unique_stack_id(str(item.get("id") or item.get("pack")), used_ids)
            surfaces.append(item)

    for spec in _split_values(args.stack):
        item = _stack_from_spec(spec, "language", used_ids)
        if item:
            stacks.append(item)
    for spec in _split_values(args.surface):
        item = _stack_from_spec(spec, "surface", used_ids)
        if item:
            if item["root"] == ".":
                item["root"] = "deploy"
            surfaces.append(item)

    if args.detect:
        try:
            detected = detect_stacks(target, packs)
        except Exception as exc:
            print(f"Warning: detection failed: {exc}")
            detected = []
        for item in detected:
            if any(s.get("pack") == item.pack and s.get("root") == item.root for s in stacks):
                continue
            stacks.append({
                "id": _unique_stack_id(item.id, used_ids),
                "pack": item.pack,
                "root": item.root,
                "kind": "language",
            })

    config = deep_merge(DEFAULT_CONFIG, old_profile or {})
    config["project"]["name"] = target.name
    if old_profile:
        config["project"]["type"] = (old_profile.get("project") or {}).get("type") or "platform"
    elif stacks:
        type_map = {
            "python-service": "service",
            "java-service": "service",
            "cpp-cli": "cli",
            "frontend-web": "frontend",
            "k8s": "platform",
        }
        config["project"]["type"] = type_map.get(str(stacks[0].get("pack")), "platform")
    else:
        config["project"]["type"] = "platform"
    config["project"]["root"] = "."
    if stacks or surfaces:
        config["stacks"] = stacks + surfaces
    elif not config.get("stacks"):
        # Old-profile fallback: synthesize a single stack from project.type.
        config["stacks"] = normalize_stacks(config, packs)
    manifest = _build_run_manifest(config, packs, target)

    if args.dry_run:
        print(json.dumps({
            "target": str(target),
            "profile": profile_name,
            "stacks": config.get("stacks", []),
            "config": config,
            "run_manifest": manifest,
        }, ensure_ascii=False, indent=2))
        return 0

    target.mkdir(parents=True, exist_ok=True)
    if (target / ".claude").exists():
        print("Warning: .claude/ already exists; TestForge files with the same names will be overwritten.")

    copies = [
        ("skills", ".claude/skills"),
        ("agents", ".claude/agents"),
        ("commands", ".claude/commands"),
        ("core", "testforge/core"),
        ("packs", "testforge/packs"),
        ("profiles", "testforge/profiles"),
        ("prompts", "testforge/prompts"),
        ("schemas", "testforge/schemas"),
        ("templates", "testforge/templates"),
        ("docs", "testforge/docs"),
        ("adapters", "testforge/adapters"),
        ("config", "testforge/config"),
        ("ci", "testforge/ci"),
    ]
    for src_rel, dst_rel in copies:
        src = SUITE_ROOT / src_rel
        if not src.exists():
            continue
        shutil.copytree(src, target / dst_rel, dirs_exist_ok=True)

    for name in ("testforge.py", "README.md", "QUICKSTART.md", "AGENTS.md", "LICENSE", "requirements-optional.txt"):
        src = SUITE_ROOT / name
        if src.exists():
            shutil.copy2(src, target / "testforge" / name)

    for folder in ("context", "cases", "runs", "reports"):
        (target / ".testforge" / folder).mkdir(parents=True, exist_ok=True)

    gitignore_path = target / ".testforge" / ".gitignore"
    if not gitignore_path.exists() or args.force:
        gitignore_path.write_text(
            "context/\nruns/\nreports/*.json\nreports/*.md\n*.db\n",
            encoding="utf-8",
        )
        print(f"Wrote ignore: {gitignore_path}")

    config_path = target / DEFAULT_CONFIG_NAME
    if config_path.exists() and not args.force:
        print(f"Keeping existing config: {config_path}")
    else:
        write_json(config_path, config)
        print(f"Wrote config: {config_path}")

    manifest_path = target / ".testforge" / "run-manifest.json"
    if manifest["suites"] and (not manifest_path.exists() or args.force or args.upgrade):
        write_json(manifest_path, manifest)
        print(f"Wrote run manifest: {manifest_path}")

    if args.with_ci:
        ci_src = SUITE_ROOT / "ci" / "github-actions.yml"
        if ci_src.exists():
            ci_dst = target / ".github" / "workflows" / "testforge.yml"
            ci_dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ci_src, ci_dst)
            print(f"Wrote CI: {ci_dst}")

    print("\nTestForge installed.")
    print("Next:")
    print("  1. Edit testforge.config.json (stacks / inputs / commands).")
    print("  2. python testforge/testforge.py doctor")
    print("  3. python testforge/testforge.py pack")
    print("  4. In Claude Code: /test-req, /test-design, /test-e2e, /test-review, /test-run")
    return 0


# ---------------------------------------------------------------------------
# pack
# ---------------------------------------------------------------------------

def cmd_pack(args: argparse.Namespace) -> int:
    config_path = normalize_config_path(args.config).resolve()
    config = load_config(str(config_path))
    root = config_root(config, str(config_path))
    inputs = as_dict(config.get("inputs"))
    ignores = [str(x) for x in as_list(inputs.get("ignore", []))]
    generation = as_dict(config.get("generation"))
    max_chars = int(generation.get("max_context_chars_per_entry", 12000) or 12000)

    entries: List[Dict[str, Any]] = []
    unsupported: List[Dict[str, str]] = []
    index = 0

    for kind, key in (("docs", "docs"), ("api", "api"), ("code", "code"), ("tests", "tests")):
        patterns = as_list(inputs.get(key, []))
        for path in expand_files(root, patterns, ignores):
            text, mode = extract_text(path)
            rel = rel_path(path, root)
            if text is None:
                unsupported.append({"source": rel, "reason": mode})
                continue
            is_markdown = path.suffix.lower() in (".md", ".markdown") or mode == "docling"
            sections = split_markdown(text) if is_markdown else [("", text)]
            for title, body in sections:
                body = body.strip()
                if not body:
                    continue
                index += 1
                content, truncated = truncate(body, max_chars)
                entry_id = f"{ID_PREFIX.get(kind, kind.upper())}-{index:04d}"
                source = rel + (f"#{slugify(title)}" if title else "")
                entries.append({
                    "id": entry_id,
                    "kind": kind,
                    "source": source,
                    "file": rel,
                    "title": title or path.name,
                    "content": content,
                    "truncated": truncated,
                    "bytes": len(body.encode("utf-8")),
                    "tokens_estimate": max(1, len(content) // 4),
                    "sha256": sha256(body),
                    "extractor": mode,
                })

    if args.with_diff:
        try:
            proc = subprocess.run(
                ["git", "-C", str(root), "diff", "--unified=3", "HEAD"],
                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30,
            )
            diff = proc.stdout.strip()
            if diff:
                index += 1
                entries.append({
                    "id": f"DIFF-{index:04d}",
                    "kind": "diff",
                    "source": "git:diff:HEAD",
                    "file": "git diff",
                    "title": "Uncommitted diff",
                    "content": truncate(diff, max_chars)[0],
                    "truncated": len(diff) > max_chars,
                    "bytes": len(diff.encode("utf-8")),
                    "tokens_estimate": max(1, len(diff) // 4),
                    "sha256": sha256(diff),
                    "extractor": "git",
                })
        except Exception as exc:
            unsupported.append({"source": "git:diff:HEAD", "reason": f"git-diff-failed: {exc}"})

    paths = as_dict(config.get("paths"))
    out_dir = Path(args.out).resolve() if args.out else (root / paths.get("context", ".testforge/context"))
    out_dir.mkdir(parents=True, exist_ok=True)

    # Attach stack metadata without changing the legacy single-stack output.
    try:
        from core.config import normalize_stacks, stack_root
        from core.packs import load_packs

        packs = load_packs(SUITE_ROOT / "packs")
        stacks = normalize_stacks(config, packs)
    except Exception:
        stacks = []
    stacks_info = [
        {"id": stack.get("id", "default"), "pack": stack.get("pack", ""), "root": stack.get("root", ".")}
        for stack in stacks
    ]
    for entry in entries:
        file_rel = entry.get("file", "")
        entry["stack_id"] = "default"
        entry["pack"] = ""
        if not file_rel or file_rel == "git diff":
            continue
        abs_file = (root / file_rel).resolve()
        matches = []
        for stack in stacks:
            sroot = stack_root(config, stack, str(config_path))
            try:
                abs_file.relative_to(sroot)
                matches.append((len(sroot.parts), stack))
            except ValueError:
                continue
        if matches:
            matched = max(matches, key=lambda item: item[0])[1]
            entry["stack_id"] = matched.get("id", "default")
            entry["pack"] = matched.get("pack", "")

    by_kind: Dict[str, int] = {}
    for entry in entries:
        by_kind[entry["kind"]] = by_kind.get(entry["kind"], 0) + 1
    payload = {
        "meta": {
            "tool": "testforge",
            "version": VERSION,
            "generated_at": now_iso(),
            "project": config.get("project", {}),
            "root": str(root),
            "max_context_chars_per_entry": max_chars,
        },
        "stats": {
            "entries": len(entries),
            "by_kind": by_kind,
            "unsupported": len(unsupported),
            "tokens_estimate": sum(e["tokens_estimate"] for e in entries),
        },
        "stacks": stacks_info,
        "entries": entries,
        "unsupported": unsupported,
    }
    write_json(out_dir / "context.json", payload)

    lines: List[str] = [
        "# TestForge Context Pack",
        "",
        f"- Generated: {payload['meta']['generated_at']}",
        f"- Project: {config.get('project', {}).get('name', '')}",
        f"- Root: `{root}`",
        f"- Entries: {len(entries)} ({by_kind})",
        f"- Unsupported: {len(unsupported)}",
        "",
        "> Every entry has a stable source reference. Cite it in test cases as `source_refs`.",
        "",
    ]
    for entry in entries:
        lang = LANG_BY_EXT.get(Path(entry["file"]).suffix.lower(), "")
        lines.append(f"## [{entry['id']}] {entry['title']}")
        lines.append("")
        lines.append(f"- source: `{entry['source']}`")
        lines.append(f"- kind: `{entry['kind']}`")
        lines.append(f"- stack: `{entry.get('stack_id', 'default')}` / pack: `{entry.get('pack', '')}`")
        lines.append(f"- extractor: `{entry['extractor']}`")
        lines.append(f"- tokens: ~{entry['tokens_estimate']}")
        if entry["truncated"]:
            lines.append("- truncated: true")
        fence = fence_for(entry["content"])
        lines.append("")
        lines.append(f"{fence}{lang}")
        lines.append(entry["content"])
        lines.append(fence)
        lines.append("")
    (out_dir / "context.md").write_text("\n".join(lines), encoding="utf-8")

    print(f"Packed {len(entries)} entries -> {out_dir}")
    print(f"  context.json / context.md")
    if unsupported:
        print(f"  {len(unsupported)} unsupported file(s):")
        for item in unsupported[:10]:
            print(f"    - {item['source']}: {item['reason']}")
        if len(unsupported) > 10:
            print("    ...")
    return 0


# ---------------------------------------------------------------------------
# validate / matrix
# ---------------------------------------------------------------------------

def load_cases(path: str) -> List[Dict[str, Any]]:
    p = Path(path)
    if not p.is_file():
        raise SystemExit(f"Cases file not found: {p}")
    data = read_json(p)
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        items = None
        for key in ("test_cases", "cases", "e2e_cases", "items"):
            if isinstance(data.get(key), list):
                items = data[key]
                break
    else:
        items = None
    if items is None:
        raise SystemExit(f"Cannot find a case list in {p} (expected test_cases/cases/e2e_cases)")
    if not all(isinstance(item, dict) for item in items):
        raise SystemExit(f"Each case in {p} must be a JSON object")
    return items


def load_requirements(path: Optional[str]) -> List[str]:
    if not path:
        return []
    p = Path(path)
    if not p.is_file():
        return []
    data = read_json(p)
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        items = data.get("requirements") or data.get("acs") or data.get("acceptance_criteria") or []
    else:
        items = []
    ids: List[str] = []
    for item in items:
        if isinstance(item, str):
            ids.append(item)
        elif isinstance(item, dict):
            value = item.get("ac_id") or item.get("id") or item.get("key")
            if value:
                ids.append(str(value))
    return ids


def get_steps(case: Dict[str, Any]) -> List[Dict[str, Any]]:
    steps = case.get("steps")
    if isinstance(steps, list) and steps:
        out: List[Dict[str, Any]] = []
        for step in steps:
            if isinstance(step, dict):
                out.append(step)
            else:
                out.append({"action": str(step), "expected": ""})
        return out
    out = []
    for key in ("given", "when", "then"):
        value = case.get(key)
        if isinstance(value, str) and value.strip():
            out.append({"action": f"{key.upper()}: {value.strip()}", "expected": ""})
        elif isinstance(value, list):
            for item in value:
                out.append({"action": f"{key.upper()}: {item}", "expected": ""})
    return out


def vague_hits(text: str) -> List[str]:
    hits = []
    for pattern in VAGUE_PATTERNS:
        if re.search(pattern, text or "", re.IGNORECASE):
            hits.append(pattern)
    return hits


def norm_title(text: str) -> str:
    text = (text or "").lower()
    text = re.sub(r"[\s\W_]+", "", text, flags=re.UNICODE)
    return text


def find_duplicates(cases: Sequence[Dict[str, Any]], threshold: float) -> List[Dict[str, Any]]:
    groups: List[Dict[str, Any]] = []
    for i in range(len(cases)):
        for j in range(i + 1, len(cases)):
            left = norm_title(str(cases[i].get("title", "")))
            right = norm_title(str(cases[j].get("title", "")))
            if not left or not right:
                continue
            ratio = difflib.SequenceMatcher(None, left, right).ratio()
            if ratio >= threshold:
                groups.append({
                    "a": cases[i].get("id") or f"case-{i + 1}",
                    "b": cases[j].get("id") or f"case-{j + 1}",
                    "similarity": round(ratio, 3),
                })
    return groups


def validate_testable_items(data: Dict[str, Any], args: argparse.Namespace) -> int:
    errors: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []
    requirements = data.get("requirements") or []
    items = data.get("testable_items") or []
    gaps = data.get("gap_list") or []
    if not isinstance(requirements, list):
        errors.append({"case": "<root>", "field": "requirements", "message": "requirements must be a list"})
        requirements = []
    if not isinstance(items, list):
        errors.append({"case": "<root>", "field": "testable_items", "message": "testable_items must be a list"})
        items = []
    if not isinstance(gaps, list):
        errors.append({"case": "<root>", "field": "gap_list", "message": "gap_list must be a list"})
        gaps = []

    req_ids: Dict[str, int] = {}
    for index, req in enumerate(requirements):
        rid = str(req.get("ac_id") or req.get("id") or f"AC-{index + 1}")
        if rid in req_ids:
            errors.append({"case": rid, "field": "ac_id", "message": "duplicate AC id"})
        else:
            req_ids[rid] = index
        for field in ("ac_id", "text"):
            if not req.get(field):
                errors.append({"case": rid, "field": field, "message": f"missing required field: {field}"})
        refs = req.get("source_refs")
        if not isinstance(refs, list) or not refs:
            errors.append({"case": rid, "field": "source_refs", "message": "source_refs must be a non-empty list"})

    ti_ids: Dict[str, int] = {}
    by_technique: Dict[str, int] = {}
    by_category: Dict[str, int] = {}
    for index, item in enumerate(items):
        tid = str(item.get("ti_id") or f"TI-{index + 1}")
        if tid in ti_ids:
            errors.append({"case": tid, "field": "ti_id", "message": "duplicate TI id"})
        else:
            ti_ids[tid] = index
        for field in ("ti_id", "description"):
            if not item.get(field):
                errors.append({"case": tid, "field": field, "message": f"missing required field: {field}"})
        ac_ids = item.get("ac_ids")
        if not isinstance(ac_ids, list) or not ac_ids:
            errors.append({"case": tid, "field": "ac_ids", "message": "ac_ids must be a non-empty list"})
        else:
            for ac in ac_ids:
                if req_ids and str(ac) not in req_ids:
                    warnings.append({"case": tid, "field": "ac_ids", "message": f"unknown AC: {ac}"})
        techniques = item.get("techniques")
        if not isinstance(techniques, list) or not techniques:
            errors.append({"case": tid, "field": "techniques", "message": "techniques must be a non-empty list"})
        else:
            for tech in techniques:
                if not isinstance(tech, str) or tech not in TECHNIQUES:
                    errors.append({"case": tid, "field": "techniques", "message": f"invalid technique: {tech}"})
                by_technique[str(tech)] = by_technique.get(str(tech), 0) + 1
        category = item.get("category")
        if category is not None and not isinstance(category, str):
            errors.append({"case": tid, "field": "category", "message": "category must be a string"})
        elif category:
            if category not in CATEGORIES:
                errors.append({"case": tid, "field": "category", "message": f"invalid category: {category}"})
            by_category[str(category)] = by_category.get(str(category), 0) + 1
        refs = item.get("source_refs")
        if not isinstance(refs, list) or not refs:
            errors.append({"case": tid, "field": "source_refs", "message": "source_refs must be a non-empty list"})

    for index, gap in enumerate(gaps):
        gid = str(gap.get("gap_id") or f"GAP-{index + 1}")
        for field in ("gap_id", "description", "impact", "owner"):
            if not gap.get(field):
                warnings.append({"case": gid, "field": field, "message": f"gap missing field: {field}"})

    if args.schema:
        schema_path = Path(args.schema)
        if not schema_path.exists():
            warnings.append({"case": "<schema>", "field": "schema", "message": f"schema not found: {schema_path}"})
        elif not module_available("jsonschema"):
            warnings.append({"case": "<schema>", "field": "schema", "message": "jsonschema not installed; skipped strict schema validation"})
        else:
            try:
                import jsonschema  # type: ignore
                jsonschema.validate(data, read_json(schema_path))
            except Exception as exc:
                errors.append({"case": "<schema>", "field": "schema", "message": str(exc)})

    report = {
        "meta": {
            "tool": "testforge",
            "version": VERSION,
            "generated_at": now_iso(),
            "kind": "testable-items",
            "file": str(Path(args.cases).resolve()),
            "requirements_file": str(Path(args.requirements).resolve()) if args.requirements else None,
        },
        "summary": {
            "requirements": len(requirements),
            "testable_items": len(items),
            "gaps": len(gaps),
            "errors": len(errors),
            "warnings": len(warnings),
            "by_technique": by_technique,
            "by_category": by_category,
        },
        "errors": errors,
        "warnings": warnings,
    }

    if args.out:
        out = Path(args.out).resolve()
    else:
        cases_path = Path(args.cases).resolve()
        if cases_path.parent.name == "cases":
            out = cases_path.parent.parent / "reports" / "testable-items-validation.json"
        else:
            out = cases_path.parent / "testable-items-validation.json"
    write_json(out, report)

    print(f"Validated testable items: {len(requirements)} AC / {len(items)} TI / {len(gaps)} gaps")
    print(f"  errors: {len(errors)}  warnings: {len(warnings)}")
    print(f"  report: {out}")
    if errors:
        for item in errors[:10]:
            print(f"  ERROR {item['case']} {item['field']}: {item['message']}")
        return 1
    if args.strict and warnings:
        print("  Strict mode: warnings treated as errors.")
        return 1
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    if not Path(args.cases).is_file():
        raise SystemExit(f"Cases file not found: {args.cases}")
    try:
        raw = read_json(Path(args.cases))
    except Exception as exc:
        raise SystemExit(f"Invalid JSON in {args.cases}: {exc}")
    kind = args.kind
    if kind == "auto":
        if isinstance(raw, dict) and "testable_items" in raw:
            kind = "testable"
        elif isinstance(raw, dict) and "e2e_cases" in raw:
            kind = "e2e"
        else:
            kind = "test-cases"
    if kind == "testable":
        if not isinstance(raw, dict):
            raise SystemExit("--kind testable expects a JSON object with testable_items")
        return validate_testable_items(raw, args)

    cases = load_cases(args.cases)
    stack_filter = getattr(args, "stack", None)
    if stack_filter:
        cases = [c for c in cases if str(c.get("stack_id") or "default") == stack_filter]
    config_path = normalize_config_path(args.config)
    config = load_config(str(config_path)) if config_path.exists() else DEFAULT_CONFIG
    gates = as_dict(config.get("quality_gates"))
    threshold = args.similarity if args.similarity is not None else float(
        gates.get("duplicate_similarity_max", 0.85) or 0.85
    )

    errors: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []
    seen_ids: Dict[str, int] = {}

    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            errors.append({"case": f"case-{index + 1}", "field": "<root>", "message": "case must be an object"})
            continue
        cid = str(case.get("id") or f"case-{index + 1}")
        if cid in seen_ids:
            errors.append({"case": cid, "field": "id", "message": f"duplicate case id (first at index {seen_ids[cid]})"})
        else:
            seen_ids[cid] = index
        is_e2e = kind == "e2e" or ("feature" in case and "technique" not in case and "type" not in case)
        required_fields = ["id", "title", "source_refs", "expected_result", "priority"]
        if is_e2e:
            required_fields.append("feature")
        else:
            required_fields.extend(["technique", "type", "automatable"])
        for field in required_fields:
            value = case.get(field)
            if value is None or (isinstance(value, str) and not value.strip()):
                errors.append({"case": cid, "field": field, "message": f"missing required field: {field}"})
        if is_e2e and not isinstance(case.get("test_data"), dict):
            errors.append({"case": cid, "field": "test_data", "message": "e2e case requires a test_data object"})
        if len(str(case.get("title", "")).strip()) < 4:
            warnings.append({"case": cid, "field": "title", "message": "title is too short"})
        source_refs = case.get("source_refs")
        if not isinstance(source_refs, list) or not source_refs:
            errors.append({"case": cid, "field": "source_refs", "message": "source_refs must be a non-empty list"})
        else:
            for ref_index, ref in enumerate(source_refs):
                if not isinstance(ref, str) or not ref.strip():
                    errors.append({"case": cid, "field": f"source_refs[{ref_index}]", "message": "source ref must be a non-empty string"})
        technique = case.get("technique")
        if technique is not None and not isinstance(technique, str):
            errors.append({"case": cid, "field": "technique", "message": "technique must be a string"})
        elif technique and technique not in TECHNIQUES:
            errors.append({"case": cid, "field": "technique", "message": f"invalid technique: {technique}"})
        priority = case.get("priority")
        if priority is not None and not isinstance(priority, str):
            errors.append({"case": cid, "field": "priority", "message": "priority must be a string"})
        elif priority and priority not in PRIORITIES:
            errors.append({"case": cid, "field": "priority", "message": f"invalid priority: {priority}"})
        case_type = case.get("type")
        if case_type is not None and not isinstance(case_type, str):
            errors.append({"case": cid, "field": "type", "message": "type must be a string"})
        elif case_type and case_type not in CASE_TYPES:
            errors.append({"case": cid, "field": "type", "message": f"invalid type: {case_type}"})
        if "automatable" in case and not isinstance(case["automatable"], bool):
            errors.append({"case": cid, "field": "automatable", "message": "automatable must be boolean"})
        if "test_data" in case and not isinstance(case["test_data"], dict):
            errors.append({"case": cid, "field": "test_data", "message": "test_data must be an object"})
        ac_ids = case.get("ac_ids")
        if ac_ids is not None and not isinstance(ac_ids, list):
            errors.append({"case": cid, "field": "ac_ids", "message": "ac_ids must be a list"})
        elif not ac_ids:
            warnings.append({"case": cid, "field": "ac_ids", "message": "no AC linked"})
        steps = get_steps(case)
        explicit_steps = isinstance(case.get("steps"), list) and bool(case.get("steps"))
        if not steps:
            errors.append({"case": cid, "field": "steps", "message": "no steps / given-when-then found"})
        for step_index, step in enumerate(steps):
            action = str(step.get("action", "") or "")
            expected = str(step.get("expected", "") or "")
            if len(action.strip()) < 2:
                errors.append({"case": cid, "field": f"steps[{step_index}].action", "message": "action is empty/too short"})
            if explicit_steps and not expected.strip():
                errors.append({"case": cid, "field": f"steps[{step_index}].expected", "message": "expected is empty"})
            for hit in vague_hits(action + " " + expected):
                warnings.append({"case": cid, "field": f"steps[{step_index}]", "message": f"vague phrase: {hit}"})
        expected_result = str(case.get("expected_result", "") or "")
        if len(expected_result.strip()) < 4:
            errors.append({"case": cid, "field": "expected_result", "message": "expected_result is too short"})
        for hit in vague_hits(expected_result):
            warnings.append({"case": cid, "field": "expected_result", "message": f"vague phrase: {hit}"})

    duplicates = find_duplicates(cases, threshold)
    max_similarity = max((d["similarity"] for d in duplicates), default=0.0)

    case_stack = {
        str(case.get("id") or f"case-{index + 1}"): str(case.get("stack_id") or "default")
        for index, case in enumerate(cases)
        if isinstance(case, dict)
    }
    by_stack: Dict[str, Dict[str, int]] = {}
    for case in cases:
        if not isinstance(case, dict):
            continue
        sid = str(case.get("stack_id") or "default")
        by_stack.setdefault(sid, {"total": 0, "errors": 0, "warnings": 0})["total"] += 1
    for item in errors:
        sid = case_stack.get(str(item.get("case")), "default")
        by_stack.setdefault(sid, {"total": 0, "errors": 0, "warnings": 0})["errors"] += 1
    for item in warnings:
        sid = case_stack.get(str(item.get("case")), "default")
        by_stack.setdefault(sid, {"total": 0, "errors": 0, "warnings": 0})["warnings"] += 1

    requirements = load_requirements(args.requirements)
    known_acs = set(requirements)
    covered = set()
    for case in cases:
        for ac in as_list(case.get("ac_ids")):
            ac_str = str(ac)
            covered.add(ac_str)
            if known_acs and ac_str not in known_acs:
                warnings.append({"case": str(case.get("id") or ""), "field": "ac_ids", "message": f"unknown AC: {ac_str}"})
    uncovered = [ac for ac in requirements if ac not in covered]
    ac_coverage = (len(requirements) - len(uncovered)) / len(requirements) if requirements else None

    if args.schema:
        schema_path = Path(args.schema)
        if not schema_path.exists():
            warnings.append({"case": "<schema>", "field": "schema", "message": f"schema not found: {schema_path}"})
        elif not module_available("jsonschema"):
            warnings.append({"case": "<schema>", "field": "schema", "message": "jsonschema not installed; skipped strict schema validation"})
        else:
            try:
                import jsonschema  # type: ignore
                schema = read_json(schema_path)
                properties = schema.get("properties", {}) if isinstance(schema, dict) else {}
                key = "e2e_cases" if "e2e_cases" in properties else "test_cases"
                jsonschema.validate({key: cases}, schema)
            except Exception as exc:
                errors.append({"case": "<schema>", "field": "schema", "message": str(exc)})

    by_type: Dict[str, int] = {}
    by_priority: Dict[str, int] = {}
    by_technique: Dict[str, int] = {}
    automatable = 0
    for case in cases:
        type_key = str(case.get("type") or ("e2e" if case.get("feature") else "unknown"))
        priority_key = str(case.get("priority") or "unknown")
        technique_key = str(case.get("technique") or "unknown")
        by_type[type_key] = by_type.get(type_key, 0) + 1
        by_priority[priority_key] = by_priority.get(priority_key, 0) + 1
        by_technique[technique_key] = by_technique.get(technique_key, 0) + 1
        if case.get("automatable") is True:
            automatable += 1

    report = {
        "meta": {
            "tool": "testforge",
            "version": VERSION,
            "generated_at": now_iso(),
            "cases_file": str(Path(args.cases).resolve()),
            "requirements_file": str(Path(args.requirements).resolve()) if args.requirements else None,
            "duplicate_threshold": threshold,
            "stack_filter": stack_filter,
        },
        "summary": {
            "total_cases": len(cases),
            "errors": len(errors),
            "warnings": len(warnings),
            "duplicates": len(duplicates),
            "max_similarity": max_similarity,
            "automatable": automatable,
            "by_type": by_type,
            "by_priority": by_priority,
            "by_technique": by_technique,
            "by_stack": by_stack,
        },
        "coverage": {
            "requirements": len(requirements),
            "covered": len(requirements) - len(uncovered) if requirements else 0,
            "uncovered": uncovered,
            "ac_coverage": ac_coverage,
        },
        "errors": errors,
        "warnings": warnings,
        "duplicates": duplicates,
    }

    if args.out:
        out = Path(args.out).resolve()
    else:
        cases_path = Path(args.cases).resolve()
        if cases_path.parent.name == "cases":
            out = cases_path.parent.parent / "reports" / "validation-report.json"
        else:
            out = cases_path.parent / "validation-report.json"
        out.parent.mkdir(parents=True, exist_ok=True)
    write_json(out, report)

    print(f"Validated {len(cases)} case(s)")
    print(f"  errors: {len(errors)}  warnings: {len(warnings)}  duplicates: {len(duplicates)}")
    if requirements:
        print(f"  AC coverage: {len(requirements) - len(uncovered)}/{len(requirements)}"
              f" ({ac_coverage:.1%})")
    print(f"  report: {out}")

    if errors:
        for item in errors[:10]:
            print(f"  ERROR {item['case']} {item['field']}: {item['message']}")
        return 1
    if args.strict and warnings:
        print("  Strict mode: warnings treated as errors.")
        return 1
    return 0


def cmd_matrix(args: argparse.Namespace) -> int:
    cases = load_cases(args.cases)
    stack_filter = getattr(args, "stack", None)
    if stack_filter:
        cases = [c for c in cases if str(c.get("stack_id") or "default") == stack_filter]
    requirements = load_requirements(args.requirements)
    matrix: Dict[str, List[str]] = {ac: [] for ac in requirements}
    matrix_by_stack: Dict[str, Dict[str, List[str]]] = {ac: {} for ac in requirements}
    orphan_cases: List[str] = []
    for case in cases:
        cid = str(case.get("id") or "")
        stack_id = str(case.get("stack_id") or "default")
        ac_ids = as_list(case.get("ac_ids"))
        if not ac_ids:
            orphan_cases.append(cid)
        for ac in ac_ids:
            ac_key = str(ac)
            matrix.setdefault(ac_key, []).append(cid)
            matrix_by_stack.setdefault(ac_key, {}).setdefault(stack_id, []).append(cid)
    uncovered = [ac for ac, ids in matrix.items() if not ids]
    uncovered_by_stack = {
        ac: [stack_id for stack_id, ids in stacks.items() if not ids]
        for ac, stacks in matrix_by_stack.items()
    }

    payload = {
        "meta": {
            "generated_at": now_iso(),
            "cases": len(cases),
            "requirements": len(requirements),
            "stack_filter": stack_filter,
        },
        "matrix": matrix,
        "matrix_by_stack": matrix_by_stack,
        "uncovered": uncovered,
        "uncovered_by_stack": uncovered_by_stack,
        "orphan_cases": orphan_cases,
    }
    out = Path(args.out).resolve() if args.out else Path(args.cases).resolve().parent / "coverage-matrix.json"
    write_json(out, payload)

    md = ["# AC Coverage Matrix", "", "| AC | Cases |", "|---|---|"]
    for ac, ids in matrix.items():
        md.append(f"| {ac} | {', '.join(ids) if ids else '**UNCOVERED**'} |")
    if uncovered:
        md.extend(["", f"Uncovered ACs: {', '.join(uncovered)}"])
    if orphan_cases:
        md.extend(["", f"Cases without AC: {', '.join(orphan_cases)}"])
    md_path = out.with_suffix(".md")
    md_path.write_text("\n".join(md), encoding="utf-8")

    print(f"Matrix -> {out}")
    print(f"  uncovered: {len(uncovered)}  orphan cases: {len(orphan_cases)}")
    return 0


# ---------------------------------------------------------------------------
# export
# ---------------------------------------------------------------------------

def flatten(value: Any) -> str:
    if isinstance(value, list):
        return "; ".join(str(v) for v in value)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)
    return "" if value is None else str(value)


def md_cell(value: Any) -> str:
    return flatten(value).replace("|", "\\|").replace("\n", " ")


def export_markdown(cases: Sequence[Dict[str, Any]], out: Path) -> Path:
    lines = [
        "# Test Cases",
        "",
        f"- Total: {len(cases)}",
        f"- Generated: {now_iso()}",
        "",
        "| ID | Title | AC | Technique | Priority | Type | Automatable |",
        "|---|---|---|---|---|---|---|",
    ]
    for case in cases:
        lines.append(
            f"| {md_cell(case.get('id'))} | {md_cell(case.get('title'))} | "
            f"{md_cell(case.get('ac_ids'))} | {md_cell(case.get('technique'))} | "
            f"{md_cell(case.get('priority'))} | {md_cell(case.get('type'))} | "
            f"{md_cell(case.get('automatable'))} |"
        )
    lines.append("")
    for case in cases:
        lines.append(f"## {case.get('id', '')} · {case.get('title', '')}")
        lines.append("")
        lines.append(f"- AC: {flatten(case.get('ac_ids'))}")
        lines.append(f"- Source: {flatten(case.get('source_refs'))}")
        lines.append(f"- Technique: {flatten(case.get('technique'))}")
        lines.append(f"- Priority: {flatten(case.get('priority'))} / Type: {flatten(case.get('type'))}")
        preconditions = case.get("preconditions") or []
        if preconditions:
            lines.append("- Preconditions:")
            for item in preconditions:
                lines.append(f"  - {item}")
        lines.append("- Steps:")
        for index, step in enumerate(get_steps(case), 1):
            action = step.get("action", "")
            expected = step.get("expected", "")
            data = step.get("data", "")
            suffix = f" (data: {data})" if data else ""
            lines.append(f"  {index}. {action}{suffix} → {expected}")
        lines.append(f"- Expected: {case.get('expected_result', '')}")
        if case.get("test_data"):
            lines.append(f"- Test data: `{json.dumps(case.get('test_data'), ensure_ascii=False)}`")
        lines.append(f"- Automatable: {case.get('automatable')}")
        if case.get("notes"):
            lines.append(f"- Notes: {case.get('notes')}")
        lines.append("")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def export_csv(cases: Sequence[Dict[str, Any]], out: Path) -> Path:
    fieldnames = [
        "id", "title", "ac_ids", "source_refs", "technique", "priority", "type",
        "preconditions", "steps", "test_data", "expected_result", "automatable", "notes",
    ]
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for case in cases:
            row = {key: case.get(key, "") for key in fieldnames}
            row["steps"] = json.dumps(get_steps(case), ensure_ascii=False)
            row["test_data"] = json.dumps(case.get("test_data", {}), ensure_ascii=False)
            for key in ("ac_ids", "source_refs", "preconditions"):
                row[key] = flatten(row[key])
            writer.writerow(row)
    return out


def export_gherkin(cases: Sequence[Dict[str, Any]], out: Path) -> Path:
    features: Dict[str, List[Dict[str, Any]]] = {}
    for case in cases:
        feature_name = str(case.get("feature") or "Generated Features")
        features.setdefault(feature_name, []).append(case)

    lines: List[str] = ["# Generated by TestForge", ""]
    for feature_name, feature_cases in features.items():
        lines.append(f"Feature: {feature_name}")
        lines.append("")
        for case in feature_cases:
            tags = [f"@{case.get('id', 'case')}"]
            if case.get("priority"):
                tags.append(f"@priority:{case['priority']}")
            if case.get("technique"):
                tags.append(f"@technique:{case['technique']}")
            lines.append("  " + " ".join(tags))
            lines.append(f"  Scenario: {case.get('title', '')}")
            for precondition in (case.get("preconditions") or []):
                lines.append(f"    Given {precondition}")
            steps = get_steps(case)
            if steps:
                for index, step in enumerate(steps):
                    keyword = "When" if index < len(steps) - 1 else "Then"
                    action = step.get("action", "")
                    expected = step.get("expected", "")
                    lines.append(f"    {keyword} {action}")
                    if index == len(steps) - 1 and expected:
                        lines.append(f"    And {expected}")
            expected_result = case.get("expected_result")
            if expected_result and not steps:
                lines.append(f"    Then {expected_result}")
            lines.append("")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def export_xlsx(cases: Sequence[Dict[str, Any]], out: Path) -> Path:
    try:
        from openpyxl import Workbook  # type: ignore
    except Exception:
        fallback = out.with_suffix(".csv")
        print("openpyxl not installed; falling back to CSV.", file=sys.stderr)
        return export_csv(cases, fallback)
    wb = Workbook()
    ws = wb.active
    ws.title = "Cases"
    headers = [
        "ID", "Title", "AC", "Source", "Technique", "Priority", "Type",
        "Preconditions", "Steps", "Test Data", "Expected", "Automatable", "Notes",
    ]
    ws.append(headers)
    for case in cases:
        steps = get_steps(case)
        step_text = "\n".join(
            f"{i}. {s.get('action', '')} -> {s.get('expected', '')}" for i, s in enumerate(steps, 1)
        )
        ws.append([
            case.get("id", ""), case.get("title", ""), flatten(case.get("ac_ids")),
            flatten(case.get("source_refs")), case.get("technique", ""), case.get("priority", ""),
            case.get("type", ""), flatten(case.get("preconditions")), step_text,
            json.dumps(case.get("test_data", {}), ensure_ascii=False),
            case.get("expected_result", ""), str(case.get("automatable", "")), case.get("notes", ""),
        ])
    for column, width in {"A": 18, "B": 40, "C": 18, "D": 40, "E": 14, "F": 10, "G": 14}.items():
        ws.column_dimensions[column].width = width
    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(str(out))
    return out


def cmd_scaffold(args: argparse.Namespace) -> int:
    from core.config import normalize_stacks, stack_root
    from core.packs import get_pack, load_packs
    from core.scaffold import scaffold_cases

    config_path = normalize_config_path(args.config).resolve()
    config = load_config(str(config_path))
    packs = load_packs(SUITE_ROOT / "packs")
    stacks = normalize_stacks(config, packs)
    stack = next((item for item in stacks if item.get("id") == args.stack), None)
    if stack is None:
        available = ", ".join(item.get("id", "") for item in stacks)
        raise SystemExit(f"Unknown stack: {args.stack} (available: {available})")
    pack = get_pack(packs, stack.get("pack", ""))
    cases = load_cases(args.cases)
    if any("stack_id" in case for case in cases):
        cases = [case for case in cases if str(case.get("stack_id") or "default") == args.stack]
    out_dir = Path(args.out)
    if not out_dir.is_absolute():
        out_dir = stack_root(config, stack, str(config_path)) / out_dir
    manifest = scaffold_cases(cases, pack, args.stack, out_dir, force=args.force)
    print(f"Scaffolded {len(manifest['written'])} file(s), skipped {len(manifest['skipped'])}")
    for item in manifest["written"]:
        print(f"  + {item['file']}")
    for item in manifest["skipped"]:
        print(f"  - {item.get('case_id')}: {item.get('reason')}")
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    from core.export_formats import export_testrail_csv, export_xray_csv

    cases = load_cases(args.cases)
    stack_filter = getattr(args, "stack", None)
    if stack_filter:
        cases = [case for case in cases if str(case.get("stack_id") or "default") == stack_filter]
    out = Path(args.out).resolve() if args.out else Path(args.cases).resolve().parent
    if out.suffix == "":
        out = out / f"test-cases.{args.format}"
    fmt = args.format
    if fmt == "markdown":
        result = export_markdown(cases, out.with_suffix(".md"))
    elif fmt == "csv":
        result = export_csv(cases, out.with_suffix(".csv"))
    elif fmt == "gherkin":
        result = export_gherkin(cases, out.with_suffix(".feature"))
    elif fmt == "xlsx":
        result = export_xlsx(cases, out.with_suffix(".xlsx"))
    elif fmt == "testrail":
        result = export_testrail_csv(cases, out.with_suffix(".csv"))
    elif fmt == "xray":
        result = export_xray_csv(cases, out.with_suffix(".csv"))
    else:
        out.parent.mkdir(parents=True, exist_ok=True)
        key = "e2e_cases" if any("feature" in case for case in cases) else "test_cases"
        write_json(out.with_suffix(".json"), {key: cases})
        result = out.with_suffix(".json")
    print(f"Exported {len(cases)} case(s) -> {result}")
    return 0


# ---------------------------------------------------------------------------
# run
# ---------------------------------------------------------------------------

def run_once(command: Any, cwd: Path, timeout: int, env: Dict[str, str]) -> Dict[str, Any]:
    started = time.time()
    try:
        proc = subprocess.run(
            command,
            shell=isinstance(command, str),
            cwd=str(cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            env=env,
        )
        return {
            "status": "passed" if proc.returncode == 0 else "failed",
            "exit_code": proc.returncode,
            "stdout": (proc.stdout or "")[-20000:],
            "stderr": (proc.stderr or "")[-20000:],
            "duration_sec": round(time.time() - started, 2),
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "status": "timeout",
            "stdout": (exc.stdout or "")[-20000:] if isinstance(exc.stdout, str) else "",
            "stderr": (exc.stderr or "")[-20000:] if isinstance(exc.stderr, str) else "",
            "duration_sec": round(time.time() - started, 2),
        }
    except Exception as exc:
        return {
            "status": "error",
            "error": str(exc),
            "duration_sec": round(time.time() - started, 2),
        }


def cmd_run(args: argparse.Namespace) -> int:
    manifest_path = Path(args.manifest).resolve()
    if not manifest_path.is_file():
        raise SystemExit(f"Manifest not found: {manifest_path}")
    try:
        manifest = as_dict(read_json(manifest_path))
    except Exception as exc:
        raise SystemExit(f"Invalid manifest JSON: {manifest_path}: {exc}")
    base = manifest_path.parent
    suites = manifest.get("suites") or []
    if getattr(args, "stack", None):
        suites = [s for s in suites if str(s.get("stack_id") or "default") == args.stack]
    if not getattr(args, "with_reports", False):
        suites = [s for s in suites if s.get("kind", "test") != "report"]
    suites = sorted(suites, key=lambda s: 0 if s.get("kind", "test") == "test" else 1)
    if not suites:
        raise SystemExit("Manifest has no suites")

    results: List[Dict[str, Any]] = []
    passed_names: set = set()
    for suite in suites:
        name = suite.get("name") or "suite"
        kind = suite.get("kind", "test")
        command = suite.get("command")
        if not command:
            results.append({"name": name, "status": "error", "error": "missing command"})
            continue
        cwd = Path(suite.get("cwd", "."))
        if not cwd.is_absolute():
            cwd = (base / cwd).resolve()
        timeout = int(suite.get("timeout", args.timeout))
        env = os.environ.copy()
        env.update({str(k): str(v) for k, v in (suite.get("env") or {}).items()})
        record: Dict[str, Any] = {
            "name": name,
            "command": command,
            "kind": kind,
            "stack_id": suite.get("stack_id", "default"),
            "pack": suite.get("pack", ""),
            "cwd": str(cwd),
            "started_at": now_iso(),
            "timeout": timeout,
            "allow_failure": bool(suite.get("allow_failure", False)),
        }
        if not args.dry_run and kind == "report":
            deps = suite.get("run_after") or []
            missing = [dep for dep in deps if dep not in passed_names]
            if missing:
                record.update({"status": "skipped", "reason": f"run_after not passed: {', '.join(missing)}"})
                results.append(record)
                print(f"[skipped] {name}: run_after not passed")
                continue
        if args.dry_run:
            record.update({"status": "dry-run", "duration_sec": 0})
            results.append(record)
            print(f"[dry-run] {name}: {command}")
            continue
        reruns = max(1, int(suite.get("reruns", 1) or 1))
        attempts: List[Dict[str, Any]] = []
        for _ in range(reruns):
            attempt = run_once(command, cwd, timeout, env)
            attempts.append(attempt)
            if attempt["status"] == "error":
                break
        statuses = [a["status"] for a in attempts]
        if "error" in statuses:
            status = "error"
        elif all(s == "passed" for s in statuses):
            status = "passed"
        elif all(s != "passed" for s in statuses):
            status = "timeout" if "timeout" in statuses else "failed"
        else:
            status = "flaky"
        last = attempts[-1]
        record.update({
            "status": status,
            "attempts": statuses,
            "reruns": reruns,
            "flaky": status == "flaky",
            "exit_code": last.get("exit_code"),
            "stdout": last.get("stdout", ""),
            "stderr": last.get("stderr", ""),
            "duration_sec": round(sum(a.get("duration_sec", 0) for a in attempts), 2),
        })
        if status == "error":
            record["error"] = last.get("error", "")
        if status == "passed":
            passed_names.add(name)
        results.append(record)
        print(f"[{record['status']}] {name} ({record['duration_sec']}s)")

    flaky_count = sum(1 for r in results if r.get("flaky"))
    by_stack: Dict[str, Dict[str, int]] = {}
    for record in results:
        sid = str(record.get("stack_id") or "default")
        bucket = by_stack.setdefault(sid, {
            "total": 0, "passed": 0, "failed": 0, "timeout": 0,
            "error": 0, "flaky": 0, "skipped": 0, "dry_run": 0,
        })
        bucket["total"] += 1
        status = str(record.get("status") or "")
        if status in bucket:
            bucket[status] += 1
    summary = {
        "total": len(results),
        "passed": sum(1 for r in results if r.get("status") == "passed"),
        "failed": sum(1 for r in results if r.get("status") == "failed"),
        "timeout": sum(1 for r in results if r.get("status") == "timeout"),
        "error": sum(1 for r in results if r.get("status") == "error"),
        "skipped": sum(1 for r in results if r.get("status") == "skipped"),
        "flaky": flaky_count,
        "flaky_rate": round(flaky_count / len(results), 4) if results else 0.0,
        "dry_run": sum(1 for r in results if r.get("status") == "dry-run"),
        "by_stack": by_stack,
    }
    payload = {"meta": {"tool": "testforge", "version": VERSION, "generated_at": now_iso(), "manifest": str(manifest_path)}, "summary": summary, "suites": results}
    out = Path(args.out).resolve() if args.out else base / "runs" / "run-results.json"
    write_json(out, payload)
    print(f"Results -> {out}")
    print(f"  passed={summary['passed']} failed={summary['failed']} timeout={summary['timeout']} error={summary['error']} flaky={summary['flaky']}")
    blocking = [
        r for r in results
        if r.get("status") in ("failed", "timeout", "error", "flaky") and not r.get("allow_failure")
    ]
    if not args.allow_failures and blocking:
        return 1
    return 0


# ---------------------------------------------------------------------------
# coverage parsing / gate
# ---------------------------------------------------------------------------

def parse_coverage(path: str) -> Optional[float]:
    p = Path(path)
    if not p.exists():
        return None
    suffix = p.suffix.lower()
    try:
        if suffix == ".json":
            data = read_json(p)
            if isinstance(data, dict):
                totals = data.get("totals")
                if isinstance(totals, dict) and "percent_covered" in totals:
                    return float(totals["percent_covered"]) / 100.0
                if "percent_covered" in data:
                    return float(data["percent_covered"]) / 100.0
                if "line_rate" in data:
                    return float(data["line_rate"])
                total = data.get("total")
                if isinstance(total, dict):
                    lines = total.get("lines")
                    if isinstance(lines, dict) and "pct" in lines:
                        return float(lines["pct"]) / 100.0
        if suffix == ".xml":
            root = ET.parse(str(p)).getroot()
            if root.tag == "report":
                for counter in root.findall("counter"):
                    if counter.get("type") == "LINE":
                        covered = int(counter.get("covered", "0"))
                        missed = int(counter.get("missed", "0"))
                        total = covered + missed
                        return covered / total if total else None
            if root.tag == "coverage" and root.get("line-rate") is not None:
                return float(root.get("line-rate"))
        if suffix == ".info":
            lf = lh = 0
            for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
                if line.startswith("LF:"):
                    lf += int(line[3:].strip() or 0)
                elif line.startswith("LH:"):
                    lh += int(line[3:].strip() or 0)
            return lh / lf if lf else None
    except Exception:
        return None
    return None


def load_mutation_score(path: Optional[str]) -> Optional[float]:
    if not path:
        return None
    p = Path(path)
    if not p.exists():
        return None
    try:
        if p.suffix.lower() == ".xml":
            root = ET.parse(str(p)).getroot()
            killed = survived = 0
            for mutation in root.iter("mutation"):
                status = str(mutation.get("status") or "").upper()
                if status == "KILLED":
                    killed += 1
                elif status == "SURVIVED":
                    survived += 1
            total = killed + survived
            return killed / total if total else None
        data = read_json(p)
        for key in ("mutation_score", "score", "mutationScore"):
            if key in data:
                value = float(data[key])
                return value / 100.0 if value > 1 else value
    except Exception:
        return None
    return None


def cmd_gate(args: argparse.Namespace) -> int:
    results_path = Path(args.results).resolve()
    if not results_path.is_file():
        raise SystemExit(f"Results not found: {results_path}")
    try:
        results = as_dict(read_json(results_path))
    except Exception as exc:
        raise SystemExit(f"Invalid results JSON: {results_path}: {exc}")
    config_file = normalize_config_path(args.config)
    has_config = config_file.exists()
    config = load_config(str(config_file)) if has_config else DEFAULT_CONFIG
    root = config_root(config, str(config_file)) if has_config else Path.cwd()
    gates = as_dict(config.get("quality_gates"))
    paths = as_dict(config.get("paths"))
    checks: List[Dict[str, Any]] = []

    def add(name: str, value: Any, threshold: Any, passed: bool, detail: str = "") -> None:
        checks.append({"name": name, "value": value, "threshold": threshold, "passed": bool(passed), "detail": detail})

    def resolve(path_value: Optional[str]) -> Optional[str]:
        if not path_value:
            return None
        candidate = Path(path_value)
        return str(candidate if candidate.is_absolute() else (root / candidate))

    # Per-stack coverage/mutation checks. Reports resolve relative to the stack root.
    try:
        packs = load_packs(SUITE_ROOT / "packs")
        stacks = normalize_stacks(config, packs)
    except Exception:
        stacks = []
    project_base = config_root(config, str(config_file)) if has_config else Path.cwd()
    for stack in stacks:
        stack_id = str(stack.get("id") or "default")
        stack_gates = as_dict(stack.get("quality_gates"))
        stack_base = project_base / (stack.get("root") or ".")
        coverage_cfg = as_dict(stack.get("coverage"))
        coverage_parser = str(coverage_cfg.get("parser") or "")
        coverage_report = str(coverage_cfg.get("report") or "")
        if coverage_parser and coverage_parser != "none" and coverage_report:
            report_path = (stack_base / coverage_report).resolve()
            value = parse_coverage(str(report_path))
            minimum = float(stack_gates.get("line_coverage_min", gates.get("line_coverage_min", 0.0)) or 0.0)
            if value is None:
                passed = bool(getattr(args, "allow_missing_reports", False))
                add(f"{stack_id}.line_coverage", None, minimum, passed, f"missing: {report_path}")
            else:
                add(f"{stack_id}.line_coverage", round(value, 4), minimum, value >= minimum)

        mutation_cfg = as_dict(stack.get("mutation"))
        mutation_parser = str(mutation_cfg.get("parser") or "")
        mutation_report = str(mutation_cfg.get("report") or "")
        if mutation_parser and mutation_parser != "none" and mutation_report:
            report_path = (stack_base / mutation_report).resolve()
            value = load_mutation_score(str(report_path))
            minimum = float(stack_gates.get("mutation_score_min", gates.get("mutation_score_min", 0.0)) or 0.0)
            if value is None:
                passed = bool(getattr(args, "allow_missing_reports", False))
                add(f"{stack_id}.mutation_score", None, minimum, passed, f"missing: {report_path}")
            else:
                add(f"{stack_id}.mutation_score", round(value, 4), minimum, value >= minimum)

    suites = as_list(results.get("suites"))
    bad = [
        s for s in suites
        if s.get("status") not in ("passed", "dry-run", "skipped") and not s.get("allow_failure")
    ]
    add("suites_passed", len(suites) - len(bad), len(suites), not bad,
        "failed: " + ", ".join(s.get("name", "?") for s in bad) if bad else "all passed")

    coverage_path = resolve(args.coverage or paths.get("coverage_report"))
    coverage = parse_coverage(coverage_path) if coverage_path else None
    if coverage is not None:
        minimum = float(gates.get("line_coverage_min", 0.0) or 0.0)
        add("line_coverage", round(coverage, 4), minimum, coverage >= minimum)
    else:
        missing = bool(coverage_path)
        passed = (not missing) or getattr(args, "allow_missing_reports", False)
        detail = f"missing coverage report: {coverage_path}" if missing else "no coverage report supplied"
        add("line_coverage", None, gates.get("line_coverage_min", 0.0), passed, detail)

    baseline = args.baseline
    if baseline is not None and coverage is not None:
        delta_min = float(gates.get("line_coverage_delta_min", 0.0) or 0.0)
        delta = coverage - float(baseline)
        add("line_coverage_delta", round(delta, 4), delta_min, delta >= delta_min)

    mutation_path = resolve(args.mutation or paths.get("mutation_report"))
    mutation = load_mutation_score(mutation_path) if mutation_path else None
    if mutation is not None:
        minimum = float(gates.get("mutation_score_min", 0.0) or 0.0)
        add("mutation_score", round(mutation, 4), minimum, mutation >= minimum)
    else:
        missing = bool(mutation_path)
        passed = (not missing) or getattr(args, "allow_missing_reports", False)
        detail = f"missing mutation report: {mutation_path}" if missing else "no mutation report supplied"
        add("mutation_score", None, gates.get("mutation_score_min", 0.0), passed, detail)

    validation_path = resolve(args.validation or paths.get("validation_report"))
    validation = None
    if validation_path and Path(validation_path).is_file():
        validation = read_json(Path(validation_path))
    if validation:
        coverage_info = validation.get("coverage") or {}
        validation_summary = validation.get("summary") or {}
        ac_cov = coverage_info.get("ac_coverage")
        if ac_cov is not None:
            minimum = float(gates.get("ac_coverage_min", 0.0) or 0.0)
            add("ac_coverage", round(float(ac_cov), 4), minimum, float(ac_cov) >= minimum)
        total = validation_summary.get("total_cases", 0)
        minimum_cases = int(gates.get("cases_min", 0) or 0)
        add("cases_count", total, minimum_cases, total >= minimum_cases)
        max_similarity = validation_summary.get("max_similarity", 0.0) or 0.0
        max_allowed = float(gates.get("duplicate_similarity_max", 1.0) or 1.0)
        add("duplicate_similarity", max_similarity, max_allowed, float(max_similarity) <= max_allowed)

    flaky_rate = (results.get("summary") or {}).get("flaky_rate")
    if flaky_rate is not None:
        maximum = float(gates.get("flaky_rate_max", 1.0) or 1.0)
        add("flaky_rate", flaky_rate, maximum, float(flaky_rate) <= maximum)

    failures = [c for c in checks if not c["passed"]]
    payload = {
        "meta": {"tool": "testforge", "version": VERSION, "generated_at": now_iso()},
        "passed": not failures,
        "checks": checks,
        "failures": failures,
        "stacks": (results.get("summary") or {}).get("by_stack") or {},
    }
    if args.out:
        out = Path(args.out).resolve()
    elif results_path.parent.name == "runs":
        out = results_path.parent.parent / "reports" / "gate-report.json"
    else:
        out = results_path.parent / "gate-report.json"
    write_json(out, payload)

    print("Quality gates:")
    for check in checks:
        mark = "PASS" if check["passed"] else "FAIL"
        print(f"  [{mark}] {check['name']}: {check['value']} (threshold {check['threshold']}) {check['detail']}")
    print(f"Report -> {out}")
    return 0 if not failures else 1


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------

def cmd_report(args: argparse.Namespace) -> int:
    results = as_dict(read_optional_json(args.results))
    validation = as_dict(read_optional_json(args.validation))
    gate = as_dict(read_optional_json(args.gate))
    matrix = as_dict(read_optional_json(args.matrix))

    lines: List[str] = [
        "# TestForge Report",
        "",
        f"- Generated: {now_iso()}",
        f"- Results: `{args.results}`",
        "",
    ]

    summary = as_dict(results.get("summary"))
    if summary:
        lines.extend([
            "## Run summary",
            "",
            "| Total | Passed | Failed | Timeout | Error | Flaky |",
            "|---:|---:|---:|---:|---:|---:|",
            f"| {summary.get('total', 0)} | {summary.get('passed', 0)} | {summary.get('failed', 0)} | "
            f"{summary.get('timeout', 0)} | {summary.get('error', 0)} | {summary.get('flaky', 0)} |",
            "",
        ])
        if summary.get("flaky"):
            lines.append(f"- Flaky rate: {float(summary.get('flaky_rate', 0)):.1%}")
            lines.append("")
        lines.extend(["### Suites", "", "| Suite | Status | Duration | Command |", "|---|---|---|---|"])
        for suite in as_list(results.get("suites")):
            lines.append(
                f"| {suite.get('name', '')} | {suite.get('status', '')} | "
                f"{suite.get('duration_sec', '')} | `{flatten(suite.get('command', ''))}` |"
            )
        lines.append("")
        by_stack = summary.get("by_stack") or {}
        if by_stack:
            lines.extend(["### By stack", "", "| Stack | Total | Passed | Failed | Flaky |", "|---|---:|---:|---:|---:|"])
            for stack_id, bucket in by_stack.items():
                lines.append(
                    f"| {stack_id} | {bucket.get('total', 0)} | {bucket.get('passed', 0)} | "
                    f"{bucket.get('failed', 0)} | {bucket.get('flaky', 0)} |"
                )
            lines.append("")

    vsummary = as_dict(validation.get("summary"))
    if vsummary:
        lines.extend([
            "## Case validation",
            "",
            f"- Total cases: {vsummary.get('total_cases', 0)}",
            f"- Errors: {vsummary.get('errors', 0)} / Warnings: {vsummary.get('warnings', 0)}",
            f"- Duplicates: {vsummary.get('duplicates', 0)} (max similarity {vsummary.get('max_similarity', 0)})",
            f"- Automatable: {vsummary.get('automatable', 0)}",
            "",
        ])
        coverage = as_dict(validation.get("coverage"))
        if coverage.get("ac_coverage") is not None:
            lines.append(f"- AC coverage: {coverage.get('covered', 0)}/{coverage.get('requirements', 0)} "
                         f"({float(coverage.get('ac_coverage', 0)):.1%})")
            lines.append("")

    gate_checks = as_list(gate.get("checks"))
    if gate_checks:
        lines.extend(["## Quality gates", "", "| Check | Value | Threshold | Result |", "|---|---:|---:|---|"])
        for check in gate_checks:
            lines.append(
                f"| {check.get('name')} | {check.get('value')} | {check.get('threshold')} | "
                f"{'PASS' if check.get('passed') else 'FAIL'} |"
            )
        lines.append("")

    uncovered = as_dict(validation.get("coverage")).get("uncovered") or as_dict(matrix).get("uncovered") or []
    if uncovered:
        lines.extend(["## Uncovered ACs", "", ", ".join(str(x) for x in uncovered), ""])

    failures = [s for s in as_list(results.get("suites")) if s.get("status") not in ("passed", "dry-run", "skipped")]
    if failures:
        lines.extend(["## Failures", ""])
        for suite in failures:
            lines.append(f"### {suite.get('name', '')} ({suite.get('status', '')})")
            lines.append("")
            log = (suite.get("stderr") or suite.get("stdout") or suite.get("error") or "")[-4000:]
            fence = fence_for(log)
            lines.append(f"{fence}text")
            lines.append(log)
            lines.append(fence)
            lines.append("")

    lines.extend([
        "## Next actions",
        "",
        "- Review errors/warnings in `validation-report.json`.",
        "- Add missing AC coverage and remove duplicates.",
        "- For failed suites, triage: product bug / test bug / environment bug.",
        "- Re-run `testforge.py gate` after fixes.",
        "",
    ])

    if args.out:
        out = Path(args.out).resolve()
    elif args.results:
        results_path = Path(args.results).resolve()
        if results_path.parent.name == "runs":
            out = results_path.parent.parent / "reports" / "report.md"
        else:
            out = results_path.parent / "report.md"
    else:
        out = Path(".testforge/reports/report.md").resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Report -> {out}")
    return 0


# ---------------------------------------------------------------------------
# MCP / prompt
# ---------------------------------------------------------------------------

def cmd_mcp(args: argparse.Namespace) -> int:
    from core.mcp import serve

    def run_cli(cli_args: List[str]) -> Tuple[int, str, str]:
        proc = subprocess.run(
            [sys.executable, str(SUITE_ROOT / "testforge.py")] + list(cli_args),
            cwd=str(Path.cwd()),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=1800,
        )
        return proc.returncode, proc.stdout or "", proc.stderr or ""

    return serve(run_cli, allow_write=args.allow_write)


def cmd_prompt(args: argparse.Namespace) -> int:
    from core.packs import load_packs
    from core.prompt import compose_prompt

    config_path = normalize_config_path(args.config).resolve()
    config = load_config(str(config_path))
    packs = load_packs(SUITE_ROOT / "packs")
    text = compose_prompt(args.stage, args.stack, config, packs, SUITE_ROOT / "prompts")
    if args.out:
        out = Path(args.out).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + "\n", encoding="utf-8")
        print(f"Prompt -> {out}")
    else:
        print(text)
    return 0


# ---------------------------------------------------------------------------
# doctor
# ---------------------------------------------------------------------------

def cmd_doctor(args: argparse.Namespace) -> int:
    print(f"TestForge {VERSION}")
    print(f"Python: {sys.version.split()[0]}")
    print(f"Suite root: {SUITE_ROOT}")
    print("")

    config_path = normalize_config_path(args.config)
    if config_path.exists():
        try:
            config = load_config(str(config_path))
            project = as_dict(config.get("project"))
            inputs = as_dict(config.get("inputs"))
            print(f"Config: OK ({config_path})")
            print(f"  project: {project.get('name')} / {project.get('type')}")
            print(f"  inputs: {', '.join(inputs.keys())}")
        except Exception as exc:
            print(f"Config: INVALID ({exc})")
    else:
        print(f"Config: not found ({config_path}) — run `testforge.py init` first")

    print("")
    print("Optional Python modules:")
    for module in ("docling", "pypdf", "docx", "openpyxl", "yaml", "pytest"):
        print(f"  {'OK' if module_available(module) else '--'} {module}")

    print("")
    print("External commands:")
    for command in ("git", "python", "pytest", "node", "npx", "docker"):
        print(f"  {'OK' if shutil.which(command) else '--'} {command}")

    print("")
    print("Pack tools:")
    try:
        if config_path.exists():
            config = load_config(str(config_path))
            packs = load_packs(SUITE_ROOT / "packs")
            for stack in normalize_stacks(config, packs):
                pack = packs.get(stack.get("pack", ""))
                if not pack:
                    continue
                print(f"  [{stack.get('id')}] {pack.id}")
                for tool in pack.tools:
                    command = str(tool.get("command") or "")
                    if not command:
                        continue
                    try:
                        proc = subprocess.run(
                            command, shell=True, capture_output=True, text=True,
                            timeout=10, encoding="utf-8", errors="replace",
                        )
                        ok = proc.returncode == 0
                    except Exception:
                        ok = False
                    print(f"    {'OK' if ok else '--'} {tool.get('name')} ({command})")
    except Exception as exc:
        print(f"  (skipped: {exc})")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="testforge",
        description="TestForge: AI test case generation & automation suite",
    )
    parser.add_argument("--version", action="version", version=f"TestForge {VERSION}")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init", help="Install TestForge into a project")
    p.add_argument("--target", default=None, help="Target project directory")
    p.add_argument("--profile", default=None,
                   choices=["platform", "service", "cli", "frontend", "backend",
                            "python-service", "java-service", "cpp-cli", "web"])
    p.add_argument("--stack", action="append", default=[], help="Pack or pack:root (repeatable/comma-separated)")
    p.add_argument("--surface", action="append", default=[], help="Surface pack, e.g. k8s (repeatable/comma-separated)")
    p.add_argument("--detect", action="store_true", help="Detect stacks from marker files")
    p.add_argument("--list-packs", action="store_true", help="List available packs")
    p.add_argument("--dry-run", action="store_true", help="Print config and manifest without writing")
    p.add_argument("--upgrade", action="store_true", help="Refresh testforge/ but preserve config and cases")
    p.add_argument("--force", action="store_true", help="Overwrite existing config")
    p.add_argument("--with-ci", action="store_true", help="Copy GitHub Actions workflow")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("pack", help="Pack docs/api/code into a structured context")
    p.add_argument("--config", default=DEFAULT_CONFIG_NAME)
    p.add_argument("--out", default=None)
    p.add_argument("--with-diff", action="store_true", help="Include git diff HEAD")
    p.set_defaults(func=cmd_pack)

    p = sub.add_parser("validate", help="Validate test cases or testable items")
    p.add_argument("--cases", required=True)
    p.add_argument("--kind", default="auto", choices=["auto", "test-cases", "e2e", "testable"],
                   help="Input kind (auto-detected by default)")
    p.add_argument("--requirements", default=None, help="JSON with AC list")
    p.add_argument("--stack", default=None, help="Filter cases by stack id")
    p.add_argument("--config", default=DEFAULT_CONFIG_NAME)
    p.add_argument("--out", default=None)
    p.add_argument("--similarity", type=float, default=None, help="Duplicate similarity threshold (0-1)")
    p.add_argument("--schema", default=None, help="Optional JSON Schema for strict validation")
    p.add_argument("--strict", action="store_true", help="Treat warnings as errors")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("matrix", help="Build AC -> case coverage matrix")
    p.add_argument("--cases", required=True)
    p.add_argument("--requirements", required=True)
    p.add_argument("--stack", default=None, help="Filter cases by stack id")
    p.add_argument("--out", default=None)
    p.set_defaults(func=cmd_matrix)

    p = sub.add_parser("export", help="Export cases to markdown/csv/gherkin/xlsx/json/testrail/xray")
    p.add_argument("--cases", required=True)
    p.add_argument("--format", default="markdown",
                   choices=["markdown", "csv", "gherkin", "xlsx", "json", "testrail", "xray"])
    p.add_argument("--stack", default=None, help="Filter cases by stack id")
    p.add_argument("--out", default=None)
    p.set_defaults(func=cmd_export)

    p = sub.add_parser("scaffold", help="Generate test skeletons from cases")
    p.add_argument("--cases", required=True)
    p.add_argument("--stack", required=True)
    p.add_argument("--out", default=".testforge/scaffold")
    p.add_argument("--config", default=DEFAULT_CONFIG_NAME)
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_scaffold)

    p = sub.add_parser("run", help="Run test suites from a manifest")
    p.add_argument("--manifest", required=True)
    p.add_argument("--out", default=None)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--stack", default=None, help="Filter suites by stack id")
    p.add_argument("--with-reports", action="store_true", help="Run kind=report suites after tests")
    p.add_argument("--timeout", type=int, default=1800)
    p.add_argument("--allow-failures", action="store_true")
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("gate", help="Check quality gates")
    p.add_argument("--results", required=True)
    p.add_argument("--config", default=DEFAULT_CONFIG_NAME)
    p.add_argument("--coverage", default=None)
    p.add_argument("--mutation", default=None)
    p.add_argument("--validation", default=None)
    p.add_argument("--baseline", type=float, default=None, help="Baseline line coverage (0-1)")
    p.add_argument("--allow-missing-reports", action="store_true", help="Do not fail on missing coverage/mutation reports")
    p.add_argument("--out", default=None)
    p.set_defaults(func=cmd_gate)

    p = sub.add_parser("report", help="Generate a markdown report")
    p.add_argument("--results", default=None)
    p.add_argument("--validation", default=None)
    p.add_argument("--gate", default=None)
    p.add_argument("--matrix", default=None)
    p.add_argument("--out", default=None)
    p.set_defaults(func=cmd_report)

    p = sub.add_parser("mcp", help="Run a stdio MCP server")
    p.add_argument("--allow-write", action="store_true", help="Allow write tools (run/scaffold/export/prompt)")
    p.set_defaults(func=cmd_mcp)

    p = sub.add_parser("prompt", help="Compose a stage prompt with pack partials")
    p.add_argument("--stack", required=True)
    p.add_argument("--stage", required=True)
    p.add_argument("--out", default=None)
    p.add_argument("--config", default=DEFAULT_CONFIG_NAME)
    p.set_defaults(func=cmd_prompt)

    p = sub.add_parser("doctor", help="Check environment and config")
    p.add_argument("--config", default=DEFAULT_CONFIG_NAME)
    p.set_defaults(func=cmd_doctor)

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
