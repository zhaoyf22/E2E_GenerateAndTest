# TestForge Universal Core + Packs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn TestForge into a universal core with composable scenario packs, shipping full Python/Java/C++ packs and frontend/K8s stubs in batch 1.

**Architecture:** Keep `TestForge/testforge.py` as the CLI and the existing engine commands, but move cross-cutting config/pack/detect/scaffold/export/MCP code into `TestForge/core/`. Add `TestForge/packs/<pack>/pack.json` plus templates/partials/adapters/CI/acceptance. `init` composes `stacks` from profiles, `--stack`, `--surface`, and `--detect`; the existing single-profile behavior remains as a synthesized single stack.

**Tech Stack:** Python 3.8+ standard library for the core; optional `jsonschema` for strict schema validation; external toolchains (pytest, Maven/Gradle, CMake/CTest) are invoked, not bundled.

**Spec:** `docs/superpowers/specs/2026-11-12-testforge-universal-core-packs-design.md`

## Global Constraints

- Python 3.8+; no new mandatory third-party Python dependency.
- Existing `testforge.config.json` without `stacks` must keep working.
- Existing profiles `platform/service/cli/frontend/backend` must keep working.
- Core must not import Java/Python/C++/frontend tooling; pack manifests own language specifics.
- All new CLI commands must support `--help`; `init`/`scaffold`/`export` must support dry-run or non-destructive defaults.
- Paths must work on Windows and POSIX; manifest `cwd` uses POSIX separators.
- MCP write tools default off; require `--allow-write` or `TESTFORGE_MCP_ALLOW_WRITE=1`.
- Tests use `unittest`; run with `cd TestForge && python -m unittest discover -s tests -v`.
- Every commit message ends with `Co-Authored-By: Claude Code <noreply@anthropic.com>`.
- Do not commit `.testforge/context/`, `.testforge/runs/`, or generated reports.

## Review Focus

- Old config with no `stacks` must not crash; it must synthesize a deterministic single stack.
- Monorepo detection must not collapse two services of the same pack into one stack.
- A pack that supports coverage but has no report must fail the gate by default, not silently pass.
- MCP `run`/`gate` must not be callable without explicit write permission.
- `scaffold` must not overwrite existing user test files unless `--force`.
- Windows paths in `run-manifest.json` must not break `cwd` resolution.
- Missing toolchains must produce a doctor hint, not a traceback.
- Prompt partials must actually be composed/read; they must not be dead files.

---

### Task 1: Core config, pack registry, and detection

**Files:**
- Create: `TestForge/core/__init__.py`
- Create: `TestForge/core/config.py`
- Create: `TestForge/core/packs.py`
- Create: `TestForge/core/detect.py`
- Create: `TestForge/schemas/config.schema.json`
- Create: `TestForge/schemas/pack.schema.json`
- Create: `TestForge/tests/__init__.py`
- Create: `TestForge/tests/test_config.py`
- Create: `TestForge/tests/test_packs.py`
- Create: `TestForge/tests/test_detect.py`
- Modify: `TestForge/testforge.py` — import helpers from `core.config`; remove local duplicates or leave thin aliases.

**Interfaces:**
- `core/config.py` exports: `DEFAULT_CONFIG_NAME`, `DEFAULT_CONFIG`, `load_config(path) -> dict`, `normalize_config_path(path) -> Path`, `deep_merge(base, override) -> dict`, `as_dict(value) -> dict`, `as_list(value) -> list`, `project_root(config, config_path) -> Path`, `normalize_stacks(config, packs) -> list[dict]`, `stack_root(config, stack, config_path) -> Path`.
- `core/packs.py` exports: `Pack` dataclass with `id`, `path`, `manifest`; properties `commands`, `inputs`, `tools`, `templates`, `scaffold`, `coverage`, `mutation`, `partials`, `adapters`, `ci`, `acceptance`; `load_pack(pack_dir) -> Pack`, `load_packs(root) -> dict[str, Pack]`, `get_pack(packs, pack_id) -> Pack`.
- `core/detect.py` exports: `DetectedStack` dataclass with `id`, `pack`, `root`, `confidence`; `detect_stacks(project_root, packs) -> list[DetectedStack]`.

- [ ] **Step 1: Write failing config tests**

`TestForge/tests/test_config.py`:

```python
import json
import tempfile
import unittest
from pathlib import Path

from core.config import load_config, normalize_stacks, project_root, stack_root


class ConfigTest(unittest.TestCase):
    def test_old_config_without_stacks_synthesizes_default(self):
        config = {"project": {"type": "service", "root": "."}, "commands": {"unit": "pytest -q"}}
        stacks = normalize_stacks(config, packs={})
        self.assertEqual(len(stacks), 1)
        self.assertEqual(stacks[0]["id"], "default")
        self.assertEqual(stacks[0]["pack"], "python-service")
        self.assertEqual(stacks[0]["commands"]["unit"], "pytest -q")

    def test_explicit_stacks_keep_ids_and_roots(self):
        config = {
            "project": {"type": "platform", "root": "."},
            "stacks": [
                {"id": "api", "pack": "python-service", "root": "services/api"},
                {"id": "svc", "pack": "java-service", "root": "services/order"},
            ],
        }
        stacks = normalize_stacks(config, packs={})
        self.assertEqual([s["id"] for s in stacks], ["api", "svc"])
        self.assertEqual(stacks[0]["root"], "services/api")

    def test_stack_root_uses_project_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "testforge.config.json").write_text(
                json.dumps({"project": {"root": "."}, "stacks": [{"id": "api", "pack": "python-service", "root": "services/api"}]}),
                encoding="utf-8",
            )
            config = load_config(str(root / "testforge.config.json"))
            stack = normalize_stacks(config, packs={})[0]
            self.assertEqual(stack_root(config, stack, str(root / "testforge.config.json")), root / "services/api")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd TestForge && python -m unittest tests.test_config -v`  
Expected: FAIL with `ModuleNotFoundError: No module named 'core'`.

- [ ] **Step 3: Implement `core/config.py`**

Copy the existing helpers from `testforge.py` (`DEFAULT_CONFIG_NAME`, `DEFAULT_CONFIG`, `load_config`, `normalize_config_path`, `deep_merge`, `as_dict`, `as_list`, `project_root`, `rel_path`). Add:

```python
def normalize_stacks(config: dict, packs: dict) -> list[dict]:
    # 1. explicit "stacks": validate unique ids, keep order, fill defaults
    # 2. no "stacks": synthesize one stack with id="default"
    #    project.type service/backend -> python-service (unless detection is supplied)
    #    cli -> cpp-cli if a cpp pack is present else python-service
    #    frontend -> frontend-web; platform -> platform profile default list
    pass


def stack_root(config: dict, stack: dict, config_path: str) -> Path:
    return (project_root(config, config_path) / stack.get("root", ".")).resolve()
```

The synthesized stack must carry `commands`, `coverage`, `mutation`, `inputs`, and `quality_gates` from the old top-level config.

- [ ] **Step 4: Run config tests to verify they pass**

Run: `cd TestForge && python -m unittest tests.test_config -v`  
Expected: 3 tests PASS.

- [ ] **Step 5: Write failing pack tests**

`TestForge/tests/test_packs.py`:

```python
import json
import tempfile
import unittest
from pathlib import Path

from core.packs import get_pack, load_pack, load_packs


class PackTest(unittest.TestCase):
    def test_load_pack_reads_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            pack_dir = Path(tmp)
            (pack_dir / "pack.json").write_text(json.dumps({
                "id": "python-service",
                "display_name": "Python Service",
                "commands": {"unit": "pytest -q"},
                "inputs": {"code": ["src/**/*.py"]},
                "tools": [{"name": "pytest", "command": "pytest --version", "required": True}],
                "scaffold": {"default_template": "pytest"},
                "coverage": {"parser": "coverage.py", "report": "coverage.json"},
                "mutation": {"parser": "json", "report": "mutation-report.json", "score_key": "mutation_score"},
            }), encoding="utf-8")
            pack = load_pack(pack_dir)
            self.assertEqual(pack.id, "python-service")
            self.assertEqual(pack.commands["unit"], "pytest -q")
            self.assertEqual(pack.coverage["parser"], "coverage.py")

    def test_load_packs_returns_all(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ("python-service", "java-service"):
                pack_dir = root / name
                pack_dir.mkdir()
                (pack_dir / "pack.json").write_text(json.dumps({"id": name}), encoding="utf-8")
            packs = load_packs(root)
            self.assertEqual(sorted(packs), ["java-service", "python-service"])
            self.assertIs(get_pack(packs, "python-service"), packs["python-service"])
```

- [ ] **Step 6: Run pack tests to verify they fail**

Run: `cd TestForge && python -m unittest tests.test_packs -v`  
Expected: FAIL with `ModuleNotFoundError: No module named 'core.packs'`.

- [ ] **Step 7: Implement `core/packs.py`**

Implement `Pack` as a `@dataclass(frozen=True)` and load `pack.json` with `json.loads`. Reject duplicate/missing ids with `ValueError`. Provide dict-returning properties; missing optional fields return `{}`/`[]`.

- [ ] **Step 8: Run pack tests to verify they pass**

Run: `cd TestForge && python -m unittest tests.test_packs -v`  
Expected: 2 tests PASS.

- [ ] **Step 9: Write failing detection tests**

`TestForge/tests/test_detect.py`:

```python
import tempfile
import unittest
from pathlib import Path

from core.detect import detect_stacks
from core.packs import Pack


def fake_pack(pack_id, files, globs=None):
    manifest = {"id": pack_id, "detect": {"files": files, "globs": globs or [], "priority": 10}}
    return Pack(id=pack_id, path=Path("."), manifest=manifest)


class DetectTest(unittest.TestCase):
    def test_detects_python_and_java_in_monorepo(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "services/api").mkdir(parents=True)
            (root / "services/api/pyproject.toml").write_text("", encoding="utf-8")
            (root / "services/order").mkdir(parents=True)
            (root / "services/order/pom.xml").write_text("", encoding="utf-8")
            packs = {
                "python-service": fake_pack("python-service", ["pyproject.toml"]),
                "java-service": fake_pack("java-service", ["pom.xml"]),
            }
            stacks = detect_stacks(root, packs)
            self.assertEqual(sorted((s.pack, s.root) for s in stacks), [
                ("java-service", "services/order"),
                ("python-service", "services/api"),
            ])

    def test_two_services_same_pack_get_unique_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ("a", "b"):
                (root / "services" / name).mkdir(parents=True)
                (root / "services" / name / "pyproject.toml").write_text("", encoding="utf-8")
            packs = {"python-service": fake_pack("python-service", ["pyproject.toml"])}
            stacks = detect_stacks(root, packs)
            self.assertEqual(len(stacks), 2)
            self.assertEqual(len({s.id for s in stacks}), 2)
```

- [ ] **Step 10: Implement `core/detect.py` and run tests**

Algorithm: recursively find `detect.files`; for each marker, root is the marker's parent (the nearest package-manifest directory); deduplicate by `(pack, root)`; sort by root depth then pack id; id = directory slug or `<pack>-<n>` when duplicate. Run:

`cd TestForge && python -m unittest tests.test_detect -v`  
Expected: 2 tests PASS.

- [ ] **Step 11: Add schemas and wire imports**

Create `schemas/config.schema.json` and `schemas/pack.schema.json` with the fields from design §7/§8. In `testforge.py`, import `load_config`, `normalize_config_path`, `deep_merge`, `as_dict`, `as_list`, `project_root`, `normalize_stacks`, `stack_root` from `core.config`; remove local duplicates. Keep aliases only if existing tests/commands need them.

- [ ] **Step 12: Run full core tests and commit**

Run: `cd TestForge && python -m unittest discover -s tests -v`  
Expected: all Task 1 tests PASS.

```bash
git add TestForge/core TestForge/schemas TestForge/tests TestForge/testforge.py
git commit -m "feat: add core config, pack registry, and stack detection

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 2: Stack-aware context, validation, and matrix

**Files:**
- Modify: `TestForge/testforge.py` — `cmd_pack`, `cmd_validate`, `cmd_matrix`
- Create: `TestForge/tests/test_stack_context.py`
- Create: `TestForge/tests/test_stack_validate.py`
- Create: `TestForge/tests/test_stack_matrix.py`
- Modify: `TestForge/schemas/test-cases.schema.json` — optional `stack_id`, `pack`, `automation`
- Modify: `TestForge/schemas/e2e-cases.schema.json` — optional `stack_id`, `pack`

**Interfaces:**
- `cmd_pack` uses `normalize_stacks` and `stack_root`; each context entry gets `stack_id` and `pack`; `context.json` gains `stacks` summary.
- `cmd_validate` groups `summary.by_stack` and accepts `--stack` filter.
- `cmd_matrix` output becomes `{ac_id: {stack_id: [case_ids]}}` plus `uncovered_by_stack`.

- [ ] **Step 1: Write failing context test**

Create a temp project with `frontend/README.md` and `services/api/requirements.md`, a config with two stacks, run `python testforge.py pack --config ... --out ...`, and assert entries have `stack_id` `web`/`api` and `source` prefixes. Use `subprocess.run([sys.executable, "testforge.py", ...], cwd=suite_root)`.

- [ ] **Step 2: Run to verify failure**

Run: `cd TestForge && python -m unittest tests.test_stack_context -v`  
Expected: FAIL — entries lack `stack_id`/`pack`.

- [ ] **Step 3: Implement stack-aware `cmd_pack`**

Loop stacks; for each stack, merge pack `inputs` + stack `inputs` + global `ignore`, expand relative to `stack_root`, create entries with `stack_id`/`pack`, and write `context.json` `stacks` summary and `context.md` per-stack sections. Keep single-stack behavior when `normalize_stacks` returns `default`.

- [ ] **Step 4: Run context test to verify pass**

Run: `cd TestForge && python -m unittest tests.test_stack_context -v`  
Expected: PASS.

- [ ] **Step 5: Write failing validation test**

Create a `test-cases.json` with two cases (`stack_id: api`, `stack_id: web`), run `validate`, assert `summary.by_stack` has both keys and `--stack api` filters to one.

- [ ] **Step 6: Implement `--stack` filter and `by_stack` grouping**

Add `--stack` to the `validate` parser. In `cmd_validate`, filter cases by `case.get("stack_id", "default")`; compute `by_stack` counts of total/errors/warnings. Keep `summary.total_cases` as the filtered total.

- [ ] **Step 7: Run validation test to verify pass**

Run: `cd TestForge && python -m unittest tests.test_stack_validate -v`  
Expected: PASS.

- [ ] **Step 8: Write failing matrix test**

Two cases: `AC-001` covered by `api`, `AC-002` covered by `web`; run `matrix`, assert:

```json
{"AC-001": {"api": ["TC-1"]}, "AC-002": {"web": ["TC-2"]}}
```

and `uncovered_by_stack` includes stacks with no case for an AC.

- [ ] **Step 9: Implement stack-aware matrix**

Add `--stack` filter. Build `matrix[ac][stack_id] = [case_ids]`. Keep a compatibility view `matrix_flat` if needed by `report`. Write Markdown with columns per stack.

- [ ] **Step 10: Run matrix test and commit**

Run: `cd TestForge && python -m unittest tests.test_stack_matrix -v`  
Expected: PASS.

```bash
git add TestForge/testforge.py TestForge/schemas TestForge/tests
git commit -m "feat: make context, validation, and matrix stack-aware

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 3: Stack-aware run, gate, and report

**Files:**
- Modify: `TestForge/testforge.py` — `cmd_run`, `cmd_gate`, `cmd_report`, `parse_coverage`, `load_mutation_score`
- Create: `TestForge/tests/test_run_stacks.py`
- Create: `TestForge/tests/test_gate_stacks.py`
- Create: `TestForge/tests/test_report_stacks.py`
- Modify: `TestForge/schemas/run-manifest.schema.json` — `stack_id`, `pack`, `kind`, `run_after`, `coverage`, `mutation`

**Interfaces:**
- Suites have `kind: "test" | "report"`; default `test`.
- `run` default runs `kind=test`; `--with-reports` runs `kind=report` after test suites; `--stack` filters.
- `gate` resolves `coverage.report`/`mutation.report` relative to stack root; `coverage.parser=none` → `not_applicable`; missing report with parser set → fail unless `--allow-missing-reports`.
- `report` groups by `stack_id`.

- [ ] **Step 1: Write failing run-kind test**

Create a temp manifest with:
```json
{"suites":[
  {"name":"test","command":"python -c \"print('test')\"","kind":"test","stack_id":"api"},
  {"name":"coverage","command":"python -c \"print('coverage')\"","kind":"report","run_after":["test"],"stack_id":"api"}
]}
```
Run without `--with-reports`; assert only `test` appears in `run-results.json`. Run with `--with-reports`; assert both appear and `coverage` starts after `test`.

- [ ] **Step 2: Implement suite `kind` and `--with-reports`**

Filter `kind=test` by default; after test suites, run report suites whose `run_after` are passed. Record `stack_id`/`pack` in results and summary.

- [ ] **Step 3: Write failing gate tests**

Create a temp config/stack with `coverage.parser="coverage.py"` and a missing report; run `gate` and assert exit 1. Add `coverage.parser="none"` and assert `not_applicable` with exit 0. Add `--allow-missing-reports` and assert exit 0 with warning.

- [ ] **Step 4: Implement parser routing and missing-report semantics**

Add `COVERAGE_PARSERS = {"coverage.py","jacoco","lcov","cobertura","istanbul","gcovr"}` and `MUTATION_PARSERS = {"json","pit-xml","stryker-json","mutmut"}`. Resolve paths with `stack_root`. Add `--allow-missing-reports`.

- [ ] **Step 5: Add PIT XML and gcovr parsing tests**

Create minimal `mutations.xml` with mutation score attributes and a `gcovr` XML; assert gate checks parse non-None values. Use small fixtures in `tests/fixtures/`.

- [ ] **Step 6: Write failing report grouping test**

Run `report` with results containing `stack_id` `api` and `web`; assert `## Stack: api` and `## Stack: web` sections.

- [ ] **Step 7: Implement report grouping and commit**

Group suites/validation/gates by stack; keep overall summary. Run:

`cd TestForge && python -m unittest tests.test_run_stacks tests.test_gate_stacks tests.test_report_stacks -v`

```bash
git add TestForge/testforge.py TestForge/schemas TestForge/tests
git commit -m "feat: stack-aware run, gate, and report

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 4: Scaffold and TestRail/Xray export

**Files:**
- Create: `TestForge/core/scaffold.py`
- Create: `TestForge/core/export_formats.py`
- Create: `TestForge/tests/test_scaffold.py`
- Create: `TestForge/tests/test_export_formats.py`
- Modify: `TestForge/testforge.py` — add `cmd_scaffold`; add `testrail`/`xray` to `cmd_export`

**Interfaces:**
- `scaffold_cases(cases, pack, stack_id, out_dir, force=False) -> dict` with `written`, `skipped`, `manifest`.
- `export_testrail_csv(cases, out) -> Path`, `export_xray_csv(cases, out) -> Path`.

- [ ] **Step 1: Write failing scaffold test**

Use a temp pack with `pack.json` `scaffold.default_template="pytest"` and `templates/pytest_test.py` containing `${id}`, `${title}`, `${steps}`, `${expected}`. Call `scaffold_cases([case], pack, "api", out_dir)`. Assert file exists, contains `@pytest.mark.skip` and the case title; run again without `force` and assert `skipped`.

- [ ] **Step 2: Implement scaffold**

Read the template, replace fixed placeholders, write `<out_dir>/<slug(title)>.py`; create `scaffold-manifest.json`; never overwrite unless `force`. Add `cmd_scaffold` parser with `--cases`, `--stack`, `--out`, `--force`.

- [ ] **Step 3: Write failing export tests**

Assert TestRail header:
`ID,Title,Section,Type,Priority,Preconditions,Steps,Expected,References`
and Xray header:
`Issue Key,Summary,Description,Test Type,Steps,Expected Result,Labels,Requirement`.
Assert steps are numbered `1. ...\n   预期: ...` and `|`/newlines are handled.

- [ ] **Step 4: Implement export formats and CLI**

Add `export_testrail_csv`/`export_xray_csv`; add `testrail`/`xray` choices to `cmd_export`; `--out` can be a directory (write `testrail.csv`/`xray.csv`).

- [ ] **Step 5: Run tests and commit**

Run: `cd TestForge && python -m unittest tests.test_scaffold tests.test_export_formats -v`

```bash
git add TestForge/core TestForge/testforge.py TestForge/tests
git commit -m "feat: add scaffold and TestRail/Xray export

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 5: MCP server and prompt composer

**Files:**
- Create: `TestForge/core/mcp.py`
- Create: `TestForge/core/prompt.py`
- Create: `TestForge/tests/test_mcp.py`
- Create: `TestForge/tests/test_prompt.py`
- Modify: `TestForge/testforge.py` — add `cmd_mcp`, `cmd_prompt`

**Interfaces:**
- `handle_request(request: dict, run_cli: Callable[[list[str]], tuple[int, str, str]]) -> dict | None`; returns JSON-RPC response or `None` for notifications.
- `TOOLS` list with names/descriptions/input schemas.
- `compose_prompt(stage: str, stack_id: str, config: dict, packs: dict, prompts_dir: Path) -> str`.

- [ ] **Step 1: Write failing MCP tests**

```python
def test_initialize_and_tools_list(self):
    resp = handle_request({"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}, lambda args: (0, "", ""))
    self.assertEqual(resp["result"]["serverInfo"]["name"], "testforge")
    resp = handle_request({"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}, lambda args: (0, "", ""))
    names = {t["name"] for t in resp["result"]["tools"]}
    self.assertTrue({"testforge_validate", "testforge_matrix", "testforge_gate", "testforge_report"}.issubset(names))

def test_write_tool_requires_permission(self):
    resp = handle_request({"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"testforge_run","arguments":{"manifest":"m.json"}}}, lambda args: (0, "", ""))
    self.assertTrue(resp["result"]["isError"])
```

- [ ] **Step 2: Implement MCP**

Implement `initialize`, `tools/list`, `tools/call`. Map tools to CLI args:
- validate → `["validate", "--cases", ...]`
- matrix → `["matrix", ...]`
- gate → `["gate", ...]`
- report → `["report", ...]`
- pack/export/scaffold/run similarly.
Read-only tools: `pack`, `validate`, `matrix`, `gate`, `report`. Write tools: `scaffold`, `export`, `run`; require `allow_write` param or env `TESTFORGE_MCP_ALLOW_WRITE=1`.
`cmd_mcp` runs a stdio loop reading JSON lines and writing JSON responses.

- [ ] **Step 3: Write failing prompt test**

Create temp `prompts/02-test-design.md` and `packs/python-service/partials/python.md`; compose; assert output contains both. Assert stack id and pack id appear.

- [ ] **Step 4: Implement prompt composer and CLI**

`cmd_prompt` parser: `--stack`, `--stage`, `--out`. Compose base prompt + partials + a short stack config block. Print to stdout when `--out` omitted.

- [ ] **Step 5: Run tests and commit**

Run: `cd TestForge && python -m unittest tests.test_mcp tests.test_prompt -v`

```bash
git add TestForge/core TestForge/testforge.py TestForge/tests
git commit -m "feat: add MCP server and prompt composer

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 6: Python service pack

**Files:**
- Create: `TestForge/packs/python-service/pack.json`
- Create: `TestForge/packs/python-service/templates/{conftest.py,pytest_test.py,testcontainers_test.py,schemathesis_test.py,hypothesis_test.py}`
- Create: `TestForge/packs/python-service/partials/python.md`
- Create: `TestForge/packs/python-service/adapters/{qodo-cover.md,pynguin.md,mutahunter.md}`
- Create: `TestForge/packs/python-service/ci/{github-actions-python.yml,gitlab-python.yml}`
- Create: `TestForge/packs/python-service/acceptance.md`
- Create: `TestForge/profiles/python-service.json`
- Create: `TestForge/examples/python-service/{pyproject.toml,requirements.json,test-cases.sample.json,src/app.py,tests/test_app.py,README.md}`
- Create: `TestForge/tests/test_pack_python.py`

**Interfaces:**
- Pack id `python-service`; commands per design §11.2; coverage `coverage.py`; mutation `mutmut`; scaffold default `pytest`.

- [ ] **Step 1: Write failing pack test**

Load pack; assert `id`, `commands["unit"] == "pytest -q"`, `coverage["parser"] == "coverage.py"`, templates include `pytest`/`conftest`/`testcontainers`/`schemathesis`/`hypothesis`, `scaffold.default_template == "pytest"`.

- [ ] **Step 2: Create pack manifest and templates**

Write `pack.json` with `inputs`, `tools`, `commands`, `coverage`, `mutation`, `templates`, `scaffold`, `prompt_partials`, `adapters`, `ci`, `acceptance`, `requires`. Templates must be valid Python with `${...}` placeholders; `pytest_test.py` must contain `@pytest.mark.skip` so scaffold output is runnable.

- [ ] **Step 3: Create profile and example**

Profile lists `stacks: [{"id":"api","pack":"python-service","root":"."}]`. Example has a minimal `add(a,b)` function and a pytest test; `test-cases.sample.json` maps AC-001.

- [ ] **Step 4: Add acceptance and run tests**

`acceptance.md` commands:
```bash
python testforge.py init --stack python-service --target <tmp> --dry-run
python -m pytest examples/python-service/tests -q
python testforge.py validate --cases examples/python-service/test-cases.sample.json --requirements examples/python-service/requirements.json
```
Run pack test and example test; expected PASS.

- [ ] **Step 5: Commit**

```bash
git add TestForge/packs/python-service TestForge/profiles/python-service.json TestForge/examples/python-service TestForge/tests/test_pack_python.py
git commit -m "feat: add python-service pack, profile, and example

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 7: Java service pack

**Files:**
- Create: `TestForge/packs/java-service/pack.json`
- Create: `TestForge/packs/java-service/templates/{JUnit5Test.java,TestcontainersTest.java,WireMockTest.java,RestAssuredTest.java}`
- Create: `TestForge/packs/java-service/partials/java.md`
- Create: `TestForge/packs/java-service/adapters/{testagent.md,testspark.md,pit.md,jqwik.md,jazzer.md}`
- Create: `TestForge/packs/java-service/ci/{github-actions-java.yml,gitlab-java.yml}`
- Create: `TestForge/packs/java-service/acceptance.md`
- Create: `TestForge/profiles/java-service.json`
- Create: `TestForge/examples/java-service/{pom.xml,requirements.json,test-cases.sample.json,src/main/java/com/example/OrderService.java,src/test/java/com/example/OrderServiceTest.java,README.md}`
- Create: `TestForge/tests/test_pack_java.py`

**Interfaces:**
- Pack id `java-service`; commands per design §11.3; coverage `jacoco`; mutation `pit-xml`; scaffold default `junit5`.

- [ ] **Step 1: Write failing pack test**

Assert `commands["unit"] == "mvn -q test"`, `coverage["parser"] == "jacoco"`, `mutation["parser"] == "pit-xml"`, templates include `junit5`/`testcontainers`/`wiremock`/`restassured`.

- [ ] **Step 2: Create pack manifest/templates**

Templates must be compilable Java with placeholders in comments/annotations; scaffold output uses `@Disabled("TestForge scaffold")`.

- [ ] **Step 3: Create profile and minimal Maven example**

`pom.xml` with JUnit 5; `OrderService` and `OrderServiceTest`; `test-cases.sample.json`; README.

- [ ] **Step 4: Test with Maven if available, otherwise dry-run**

Run `mvn -q test` in example; if Maven missing, `python testforge.py init --stack java-service --target <tmp> --dry-run` and `python -m unittest tests.test_pack_java -v`.

- [ ] **Step 5: Commit**

```bash
git add TestForge/packs/java-service TestForge/profiles/java-service.json TestForge/examples/java-service TestForge/tests/test_pack_java.py
git commit -m "feat: add java-service pack, profile, and example

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 8: C++ CLI pack

**Files:**
- Create: `TestForge/packs/cpp-cli/pack.json`
- Create: `TestForge/packs/cpp-cli/templates/{gtest_test.cpp,catch2_test.cpp,CMakeLists.test.cmake,mull.yml,fuzztest.cpp,rapidcheck_test.cpp,approvaltests_test.cpp,cli11_test.cpp}`
- Create: `TestForge/packs/cpp-cli/partials/cpp.md`
- Create: `TestForge/packs/cpp-cli/adapters/{utbotcpp.md,citywalk.md,unittest-generator-mcp.md,cpp-utgen.md,testcontainers-native.md}`
- Create: `TestForge/packs/cpp-cli/ci/{github-actions-cpp.yml,gitlab-cpp.yml}`
- Create: `TestForge/packs/cpp-cli/acceptance.md`
- Create: `TestForge/profiles/cpp-cli.json`
- Create: `TestForge/examples/cpp-cli/{CMakeLists.txt,requirements.json,test-cases.sample.json,src/main.cpp,tests/test_main.cpp,README.md}`
- Create: `TestForge/tests/test_pack_cpp.py`

**Interfaces:**
- Pack id `cpp-cli`; commands per design §11.4; coverage `lcov`; mutation `json` (Mull report); scaffold default `gtest`.

- [ ] **Step 1: Write failing pack test**

Assert `commands["unit"].startswith("ctest")`, `coverage["parser"] == "lcov"`, `mutation["tool"] == "mull"`, templates include `gtest`/`catch2`/`cmake`/`mull`/`fuzztest`/`rapidcheck`/`approvaltests`/`cli11`.

- [ ] **Step 2: Create pack manifest/templates**

Templates must compile with C++20; scaffold output uses `DISABLED_` prefix or `GTEST_SKIP()`.

- [ ] **Step 3: Create profile and minimal CMake example**

`CMakeLists.txt` with GoogleTest via FetchContent or find_package; `main.cpp` with CLI11; `test_main.cpp`; `test-cases.sample.json`; README.

- [ ] **Step 4: Test with CMake if available, otherwise dry-run**

Run `cmake -S examples/cpp-cli -B build` + `ctest`; if missing, run init dry-run and pack test.

- [ ] **Step 5: Commit**

```bash
git add TestForge/packs/cpp-cli TestForge/profiles/cpp-cli.json TestForge/examples/cpp-cli TestForge/tests/test_pack_cpp.py
git commit -m "feat: add cpp-cli pack, profile, and example

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 9: Frontend and K8s stub packs

**Files:**
- Create: `TestForge/packs/frontend-web/pack.json`
- Create: `TestForge/packs/frontend-web/templates/.gitkeep`
- Create: `TestForge/packs/frontend-web/partials/frontend.md`
- Create: `TestForge/packs/frontend-web/acceptance.md`
- Create: `TestForge/packs/k8s/pack.json`
- Create: `TestForge/packs/k8s/templates/.gitkeep`
- Create: `TestForge/packs/k8s/partials/k8s.md`
- Create: `TestForge/packs/k8s/acceptance.md`
- Create: `TestForge/profiles/web.json`
- Create: `TestForge/tests/test_pack_stubs.py`

**Interfaces:**
- Both packs must load, list, and support `init --dry-run`; full templates arrive in batch 2.
- `frontend-web` commands: `vitest`, `playwright`, `a11y`, `visual`, `coverage` (istanbul).
- `k8s` commands: `chainsaw`, `orchestrate`, `chaos`; coverage/mutation `none`.

- [ ] **Step 1: Write failing stub tests**

`load_packs` returns 5 packs; `load_pack(frontend-web)` has `coverage.parser == "istanbul"`; `load_pack(k8s)` has `coverage.parser == "none"`; `init --stack frontend-web --dry-run` exits 0 and prints a config with one stack.

- [ ] **Step 2: Create stub manifests/partials/acceptance**

Keep `templates/.gitkeep`; acceptance states "batch 2". `k8s` coverage/mutation `{"parser":"none"}`.

- [ ] **Step 3: Run tests and commit**

Run: `cd TestForge && python -m unittest tests.test_pack_stubs -v`

```bash
git add TestForge/packs/frontend-web TestForge/packs/k8s TestForge/profiles/web.json TestForge/tests/test_pack_stubs.py
git commit -m "feat: add frontend-web and k8s pack stubs

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 10: Init composition, CLI, docs, CI, and full acceptance

**Files:**
- Modify: `TestForge/testforge.py` — `cmd_init`, `build_parser`, `cmd_doctor`
- Create: `TestForge/tests/test_init.py`
- Create: `TestForge/profiles/platform.json` (composition of web + python + java + k8s)
- Modify: `TestForge/README.md`, `QUICKSTART.md`, `AGENTS.md`, `docs/WORKFLOW.md`, `docs/QUALITY-GATES.md`, `docs/REVIEW-2026-11-10.md`
- Create: `TestForge/ci/github-actions-python.yml`, `github-actions-java.yml`, `github-actions-cpp.yml`
- Create: `TestForge/examples/README.md` update

**Interfaces:**
- `init` flags: `--profile`, `--stack` (repeatable/comma), `--surface`, `--detect`, `--list-packs`, `--dry-run`, `--upgrade`, `--force`, `--with-ci`.
- `doctor --json` optional; default human table.
- `profiles/platform.json` has `stacks: [frontend-web, python-service, java-service, cpp-cli]`, `surfaces: [k8s]`.

- [ ] **Step 1: Write failing init tests**

- `test_list_packs_lists_five`
- `test_init_dry_run_with_stack_produces_config`
- `test_init_detect_composes_monorepo_stacks`
- `test_init_old_profile_still_works`
- `test_init_upgrade_preserves_config_and_cases`

Use `subprocess.run` with `--dry-run`; parse stdout JSON.

- [ ] **Step 2: Implement init composition**

Parse profile JSON, `--stack pack`/`pack:root`, `--surface`, `--detect`. Merge detected stacks, deduplicate by `(pack, root)`, keep explicit ids. Generate config with `stacks`; generate run manifest with `kind=test|report` suites and `cwd` relative to `.testforge`; copy `core`, `packs`, `profiles`, `schemas`, `prompts`, `templates`, `adapters`, `ci`, `docs`, `config`, `.claude/*`; write `.testforge/.gitignore`; `--dry-run` prints JSON and writes nothing; `--upgrade` refreshes `testforge/` but preserves config/cases.

- [ ] **Step 3: Implement doctor per pack**

Iterate stacks; for each `pack.tools`, run `tool["command"]` with timeout 10s; record `ok/missing` and `install`. Do not fail if missing.

- [ ] **Step 4: Update CLI parser and docs**

Add `--stack` to `validate`/`matrix`/`run`/`export`; add `--with-reports` to `run`; add `--allow-missing-reports` to `gate`; add `--allow-write` to `mcp`; add `prompt`/`scaffold` subcommands. Update README/QUICKSTART/AGENTS/WORKFLOW/QUALITY-GATES/REVIEW with the new universal-core + packs model and batch 1 scope.

- [ ] **Step 5: Add CI templates**

GitHub Actions for Python (`pytest` + coverage), Java (`mvn test` + JaCoCo), C++ (`cmake` + `ctest` + lcov), each with `testforge validate`/`gate`. GitLab equivalents optional.

- [ ] **Step 6: Run full acceptance**

```bash
cd TestForge
python -m unittest discover -s tests -v

python testforge.py --help
python testforge.py init --list-packs
python testforge.py init --stack python-service --target <tmp> --dry-run
python testforge.py init --stack java-service --target <tmp> --dry-run
python testforge.py init --stack cpp-cli --target <tmp> --dry-run
python testforge.py init --profile platform --target <tmp> --dry-run

python testforge.py validate --cases examples/platform/testable-items.sample.json --kind testable
python testforge.py validate --cases examples/platform/test-cases.sample.json --requirements examples/platform/requirements.json
python testforge.py export --cases examples/platform/e2e-cases.sample.json --format gherkin --out <tmp>/e2e.feature
python testforge.py export --cases examples/platform/test-cases.sample.json --format testrail --out <tmp>/testrail.csv
python testforge.py export --cases examples/platform/test-cases.sample.json --format xray --out <tmp>/xray.csv
python testforge.py run --manifest examples/platform/run-manifest.sample.json --dry-run
```

Expected: all unit tests pass; each dry-run exits 0; old examples still validate/export; TestRail/Xray headers match; MCP tests pass.

- [ ] **Step 7: Commit**

```bash
git add TestForge
git commit -m "feat: compose init from universal core and packs

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

## Self-Review

- **Spec coverage:** Tasks 1–5 cover core config/packs/detect/scaffold/export/MCP/prompt; Tasks 6–8 cover the three full packs; Task 9 covers frontend/K8s stubs; Task 10 covers init composition, doctor, docs, CI, acceptance. Batch 1 acceptance in design §15/§16 is mapped.
- **Step scan:** Each task has failing test → run → implement → pass → commit. Tests carry exact assertions; code steps name signatures and files, not full bodies.
- **Type consistency:** `Pack` properties, `normalize_stacks`, `stack_root`, `scaffold_cases`, `export_testrail_csv`, `handle_request`, and `compose_prompt` are defined once and referenced consistently.
- **Review Focus:** Old config, monorepo duplicates, missing coverage false GO, MCP write permission, scaffold overwrite, Windows cwd, missing toolchains, prompt partials all have owning tests.
- **Proportion:** The plan specifies interfaces and tests; code bodies are left to the implementer except where exact values matter (headers, placeholder sets, commands).
