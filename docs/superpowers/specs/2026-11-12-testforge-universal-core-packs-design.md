# TestForge 通用内核 + 场景包（Packs）设计

> 日期：2026-11-12  
> 状态：待批准  
> 范围：把现有 `TestForge/` 从“单一 profile 套件”升级为“通用内核 + 可组合场景包”，覆盖平台项目、Python 服务、Java 服务、C++ 客户端工具、Kubernetes 集群测试。  
> 实现位置：`TestForge/`  
> 设计文档位置：`docs/superpowers/specs/2026-11-12-testforge-universal-core-packs-design.md`

---

## 1. 背景与意图

现有 TestForge 已具备：

- `pack`：需求/设计/API/代码 → 带 `source_refs` 的上下文；
- `validate`：testable-items / test-cases / e2e-cases 校验；
- `matrix`：AC → 用例覆盖矩阵；
- `export`：Markdown/CSV/Gherkin/JSON/XLSX；
- `run`：多套件执行、reruns/flaky；
- `gate`：AC 覆盖、重复度、行覆盖、变异分、flaky；
- `report`：Markdown 报告；
- `init`：platform/service/cli/frontend/backend 五种 profile；
- prompts / skills / subagents / commands / templates / adapters / CI / examples。

它的不足不是“没有主流程”，而是**语言/框架/集群差异被塞进了单一 profile 和单一模板目录**，导致：

1. 新增 Java/C++/K8s 场景时要复制或分叉；
2. 一个项目同时有前端、Python、Java、C++、集群时，无法用一个配置表达；
3. 跨栈追溯（一个 AC 同时被 Web E2E、Java API、Python worker、C++ CLI 覆盖）做不到；
4. 每种语言的覆盖率格式、测试命令、模板、门禁指标不同，单体条件分支会失控。

**意图：** 把“通用”和“专用”分开：通用内核只认契约和编排；场景包（pack）拥有语言/工具细节。初始化时选择/检测 pack，组合成一个项目配置。

---

## 2. 目标、非目标、反目标

### 2.1 目标

1. 一个 `testforge.config.json` 能同时声明多个 stack（web / python / java / cpp / k8s）。
2. `init` 支持 `--profile`、`--stack`、`--surface`、`--detect` 组合装配。
3. 每个 pack 自带：检测规则、命令、覆盖率/变异解析、模板、提示词 partial、适配器、CI、验收。
4. 跨 stack 的 AC 追溯、用例矩阵、运行编排、门禁、报告。
5. 现有配置、schema、示例、命令保持向后兼容。
6. 内核仍是 Python 3.8+ 标准库优先；pack 的外部工具按需安装。
7. 提供 `scaffold`、`export testrail|xray`、`mcp` 三个“接入实际项目”能力。

### 2.2 非目标

- 不自研通用测试生成大模型；生成交给宿主 Agent 和专用工具（Playwright Agents、TestAgent、TestSpark、UTBotCpp、Qodo Cover 等）。
- 不打包 Maven/Gradle/CMake/Node/Python 工具链；只调用项目已有工具。
- 不实现浏览器、K8s、混沌引擎；只编排和断言。
- 不替代 TestRail/Xray/Kiwi TCMS。
- 不在本迭代覆盖 LLM/RAG/Agent 产品评测（保留为后续 pack）。

### 2.3 反目标（即使技术可行也算失败）

- 内核出现大量 `if language == "java"` 分支。
- 每个 pack 只是“文档 + 空模板”，跑不起来。
- 为了通用而牺牲可执行性：模板不能编译、命令不能 dry-run、门禁无法解析。
- 一个巨型万能 prompt 取代“通用骨架 + pack partial”。
- 破坏现有用户配置和示例。

---

## 3. 约束

1. **兼容性**：现有 `project/inputs/commands/quality_gates/paths` 配置继续可用；无 `stacks` 时按单 stack 处理。
2. **依赖**：核心 CLI 不强制新增 Python 依赖；`jsonschema`/`openpyxl`/Docling 仍为可选。
3. **平台**：Windows（PowerShell/Git Bash）、Linux、macOS 都能运行；路径使用 `pathlib`，manifest `cwd` 用 POSIX 相对路径。
4. **安全**：MCP 默认只读；`run`/`gate` 需要显式授权；命令只来自 manifest，不接受任意 shell 注入。
5. **许可证**：jqwik 1.10+ 有 Anti-AI Usage Clause；Qodo Cover 对 C++ 非官方支持；Playwright Agents/healer 可能放宽断言；这些必须在适配器中标注。
6. **交付**：每个 pack 必须有可执行的 acceptance 脚本/命令，不能只写文档。

---

## 4. 方案选择

### 方案 A：通用内核 + 场景包（已选）

- 内核：契约、检测、编排、校验、门禁、报告、MCP、导出。
- Pack：语言/工具细节。
- Profile：pack 组合。
- 优点：一套契约、跨栈追溯、加场景只加 pack。
- 代价：需要一次抽象；每个 pack 要做验收。

### 方案 B：单体通用套件 + 大量条件分支

- 优点：短期快。
- 缺点：`if java / if cpp / if k8s` 会迅速失控，覆盖率解析、命令、模板都耦合。
- 不选。

### 方案 C：每个场景一套独立套件

- 优点：每套简单。
- 缺点：重复严重，跨栈追溯和统一门禁做不了。
- 不选。

**结论：A。** 本设计按 A 展开。

---

## 5. 总体架构

```text
┌─────────────────────────────────────────────────────────────┐
│ core（语言无关）                                             │
│  contracts/  schemas + 数据模型                              │
│  detect/     从文件标记识别 stack                             │
│  engine/     pack / validate / matrix / run / gate / report   │
│  scaffold/   用例 → 测试骨架（按 pack 模板）                   │
│  export/     testrail / xray / markdown / gherkin / json      │
│  mcp/        stdio JSON-RPC，暴露工具                          │
│  prompts/    通用提示词骨架 + partial 注入点                   │
└───────────────────────────────┬─────────────────────────────┘
                                │ pack.json 契约
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌───────────────┐       ┌───────────────┐       ┌───────────────┐
│ frontend-web  │       │ python-service│       │ java-service  │
│ Vitest/Playwright │   │ pytest/uv     │       │ Maven/Gradle  │
└───────────────┘       └───────────────┘       └───────────────┘
        ┌───────────────────────┬───────────────────────┐
        ▼                       ▼
┌───────────────┐       ┌───────────────┐
│   cpp-cli     │       │      k8s      │
│ CMake/CTest   │       │ Testkube/     │
│ GoogleTest/Mull│      │ Chainsaw      │
└───────────────┘       └───────────────┘
```

### 5.1 核心原则

1. **内核只认契约**：不 import Java/Python/C++ 工具，不做语言判断。
2. **Pack 拥有差异**：命令、覆盖率解析、模板、prompt partial、适配器、CI、验收。
3. **Stack 是项目中的一个可测试单元**：`frontend`、`api`、`svc`、`cli`、`k8s`。
4. **一个 AC 可跨 stack**：用例带 `stack_id`，矩阵聚合。
5. **缺失工具不阻塞**：`doctor` 提示；`run --dry-run` 可用；`gate` 跳过未提供的指标。

---

## 6. 目录结构

```text
TestForge/
├── testforge.py                 # CLI 入口，参数解析 + 调度 core
├── core/
│   ├── __init__.py
│   ├── config.py                # 配置加载/合并/向后兼容
│   ├── detect.py                # stack/pack 自动检测
│   ├── pack.py                  # pack.json 加载、校验、组合
│   ├── context.py               # pack 命令（上下文打包）
│   ├── validate.py              # testable/test-cases/e2e 校验
│   ├── matrix.py                # 跨 stack AC 矩阵
│   ├── scaffold.py              # 用例 → 测试骨架
│   ├── export.py                # testrail/xray/markdown/gherkin/json
│   ├── run.py                   # 多 stack 运行
│   ├── gate.py                  # 覆盖率/变异/flaky/AC 门禁
│   ├── report.py                # 跨 stack 报告
│   ├── mcp.py                   # stdio MCP server
│   └── self_test.py             # pack acceptance 自检（可选）
├── packs/
│   ├── frontend-web/
│   │   ├── pack.json
│   │   ├── templates/
│   │   ├── partials/
│   │   ├── adapters/
│   │   ├── ci/
│   │   └── acceptance.md
│   ├── python-service/
│   ├── java-service/
│   ├── cpp-cli/
│   └── k8s/
├── profiles/
│   ├── platform.json
│   ├── python-service.json
│   ├── java-service.json
│   ├── cpp-cli.json
│   └── web.json
├── schemas/
│   ├── testable-items.schema.json
│   ├── test-cases.schema.json
│   ├── e2e-cases.schema.json
│   ├── run-manifest.schema.json
│   ├── config.schema.json        # 新增
│   └── pack.schema.json          # 新增
├── prompts/                      # 通用骨架
├── skills/ agents/ commands/     # 现有，更新路由
├── templates/                    # 通用模板（保留）
├── adapters/                     # 通用适配器（保留）
├── ci/                           # 通用 CI
├── examples/
│   ├── platform/
│   ├── python-service/
│   ├── java-service/
│   ├── cpp-cli/
│   └── k8s/
└── docs/
```

> `init` 会把 `core/`、`packs/`、`profiles/`、`schemas/`、`prompts/` 复制到目标项目的 `testforge/` 下；目标项目只保留 `testforge.config.json` 和 `.testforge/` 运行产物。

---

## 7. 配置模型

### 7.1 新配置（多 stack）

```json
{
  "project": {
    "name": "my-platform",
    "type": "platform",
    "root": "."
  },
  "stacks": [
    {
      "id": "web",
      "pack": "frontend-web",
      "root": "frontend",
      "commands": { "e2e": "npx playwright test" }
    },
    {
      "id": "api",
      "pack": "python-service",
      "root": "services/api",
      "commands": { "unit": "uv run pytest -q" }
    },
    {
      "id": "svc",
      "pack": "java-service",
      "root": "services/order",
      "commands": { "unit": "mvn -q test" }
    },
    {
      "id": "cli",
      "pack": "cpp-cli",
      "root": "tools/cli",
      "commands": { "unit": "ctest --test-dir build --output-on-failure" }
    },
    {
      "id": "k8s",
      "pack": "k8s",
      "root": "deploy",
      "commands": { "e2e": "chainsaw test" }
    }
  ],
  "quality_gates": {
    "ac_coverage_min": 0.9,
    "duplicate_similarity_max": 0.85,
    "line_coverage_min": 0.6,
    "mutation_score_min": 0.6,
    "flaky_rate_max": 0.02
  },
  "paths": {
    "context": ".testforge/context",
    "cases": ".testforge/cases",
    "runs": ".testforge/runs",
    "reports": ".testforge/reports"
  }
}
```

### 7.2 Stack 字段

| 字段 | 必填 | 说明 |
|---|---|---|
| `id` | 是 | 项目内唯一，如 `web`/`api`/`svc`/`cli`/`k8s` |
| `pack` | 是 | pack id |
| `root` | 否 | 相对项目根；默认 `.` |
| `commands` | 否 | 覆盖 pack 默认命令 |
| `coverage` | 否 | 覆盖 `{parser, report}` |
| `mutation` | 否 | 覆盖 `{tool, report, score_key}` |
| `quality_gates` | 否 | 覆盖全局阈值 |
| `inputs` | 否 | 覆盖 pack 默认输入 glob |
| `tags` | 否 | 用于 `run --tag` 过滤 |

### 7.3 向后兼容

- 无 `stacks`：按 `project.type` 合成单 stack：
  - `platform` → `frontend-web` + `python-service` + `k8s`（或按检测）
  - `service` → `python-service` 或 `java-service`（按检测）
  - `cli` → `cpp-cli`（若 CMake/CTest 检测到）或 `python-service`
  - `frontend` → `frontend-web`
  - `backend` → `python-service` 或 `java-service`
- 旧 `inputs/commands/quality_gates` 直接映射到单 stack。
- 旧 `test-cases.json` 无 `stack_id` 仍可校验/导出；`matrix` 归入 `default` stack。

---

## 8. Pack 契约

### 8.1 `pack.json`

```json
{
  "id": "python-service",
  "display_name": "Python Service",
  "version": "1.0.0",
  "detect": {
    "files": ["pyproject.toml", "requirements.txt", "setup.py", "setup.cfg"],
    "globs": ["**/*.py"],
    "priority": 10
  },
  "commands": {
    "unit": "pytest -q",
    "api": "pytest tests/api -q",
    "coverage": "pytest --cov=src --cov-report=json:coverage.json",
    "mutation": "mutmut run"
  },
  "coverage": {
    "parser": "coverage.py",
    "report": "coverage.json"
  },
  "mutation": {
    "tool": "mutmut",
    "report": "mutation-report.json",
    "score_key": "mutation_score"
  },
  "templates": [
    { "id": "pytest", "path": "templates/pytest_test.py", "target": "tests/test_${module}.py" },
    { "id": "conftest", "path": "templates/conftest.py", "target": "tests/conftest.py" },
    { "id": "testcontainers", "path": "templates/testcontainers_test.py", "target": "tests/integration/test_${module}_container.py" },
    { "id": "schemathesis", "path": "templates/schemathesis_test.py", "target": "tests/contract/test_openapi.py" },
    { "id": "hypothesis", "path": "templates/hypothesis_test.py", "target": "tests/property/test_${module}_property.py" }
  ],
  "prompt_partials": ["partials/python.md"],
  "adapters": ["adapters/qodo-cover.md", "adapters/pynguin.md", "adapters/mutahunter.md"],
  "ci": ["ci/github-actions-python.yml", "ci/gitlab-python.yml"],
  "acceptance": "acceptance.md",
  "requires": ["python>=3.10", "pytest", "coverage"]
}
```

### 8.2 Pack 职责

Pack 必须提供：

1. **detect**：文件标记和 glob；用于 `init --detect`。
2. **commands**：`unit`/`integration`/`api`/`e2e`/`coverage`/`mutation`，可被 stack 覆盖。
3. **coverage/mutation**：解析器 id + 报告路径 + 分数 key。
4. **templates**：模板 id、源文件、目标路径（支持 `${module}`/`${stack}` 占位）。
5. **prompt_partials**：语言/框架特定规则，注入通用 prompt。
6. **adapters**：外部工具接入说明（Playwright Agents、TestAgent、UTBotCpp 等）。
7. **ci**：GitHub/GitLab 片段。
8. **acceptance**：该 pack 的验收命令和预期。

### 8.3 内核不做什么

- 不硬编码语言/框架。
- 不解析具体语言的 AST（交给 pack/外部工具）。
- 不安装/升级工具链。
- 不假设覆盖率格式（由 `coverage.parser` 路由）。

---

## 9. Core CLI 契约

### 9.1 `init`

```bash
python testforge.py init --target . \
  --stack python-service \
  --stack java-service \
  --surface k8s \
  --with-ci
```

选项：

| 选项 | 说明 |
|---|---|
| `--profile platform|python-service|java-service|cpp-cli|web` | 预置组合 |
| `--stack <pack>` | 可重复/逗号分隔 |
| `--surface <pack>` | 非语言层（k8s） |
| `--detect` | 从文件标记自动识别 stack |
| `--list-packs` | 列出可用 pack |
| `--dry-run` | 只打印将生成的配置/文件 |
| `--force` | 覆盖现有配置 |
| `--with-ci` | 复制对应 CI |

行为：

1. 解析/合并 profile、`--stack`、`--surface`、检测结果。
2. 复制 `core/`、`packs/`、`profiles/`、`schemas/`、`prompts/` 到 `target/testforge/`。
3. 生成 `testforge.config.json`，每个 stack 带 `root`、`pack`、默认命令。
4. 生成 `.testforge/run-manifest.json`，每个 stack 一个或多个 suite，`cwd` 指向 stack root。
5. 生成 `.testforge/.gitignore`。
6. 不自动覆盖目标项目已有测试文件；模板通过 `template`/`scaffold` 写入。

### 9.2 `pack`

- 按 stack root + pack `inputs` + 全局 ignore 收集文件。
- 上下文条目增加 `stack_id`、`pack`。
- `context.json` 增加 `stacks` 分组；`context.md` 按 stack 分节。
- 兼容旧配置（单 stack）。

### 9.3 `validate`

- `--kind auto|testable|test-cases|e2e`。
- 按 stack 分组统计；错误/警告带 `stack_id`。
- `--schema` 仍可选。
- 兼容无 `stack_id` 的旧用例。

### 9.4 `matrix`

- 输出 AC × stack 矩阵：
  ```json
  {
    "AC-001": {
      "web": ["E2E-001"],
      "api": ["TC-API-003"],
      "svc": [],
      "cli": []
    }
  }
  ```
- `--stack` 过滤；`--format markdown|json`。
- 未覆盖 AC 按 stack 标注。

### 9.5 `scaffold`

```bash
python testforge.py scaffold \
  --cases .testforge/cases/e2e-cases.json \
  --stack web \
  --out e2e/tests/generated
```

- 按 stack 的 pack 模板生成**可编译/可跳过**的骨架：
  - frontend-web → Playwright spec（`test.fixme`/`test.skip` + 步骤注释）；
  - python-service → pytest（`@pytest.mark.skip`）；
  - java-service → JUnit 5（`@Disabled`）；
  - cpp-cli → GoogleTest（`DISABLED_` 前缀）；
  - k8s → Chainsaw YAML（`skip: true` 或注释）。
- 不调用 LLM；确定性输出。
- `--force` 覆盖；默认跳过已存在文件。
- 生成清单 `.testforge/scaffold-manifest.json`。

### 9.6 `template`

```bash
python testforge.py template \
  --pack python-service \
  --id conftest \
  --out tests/conftest.py
```

- 从 `packs/<pack>/templates/` 复制单个模板到目标路径。
- 支持 `${module}`/`${stack}` 占位；无占位时原样复制。
- 不覆盖已有文件，除非 `--force`。

### 9.7 `export`

| 格式 | 说明 |
|---|---|
| `markdown` | 现有 |
| `csv` | 现有通用 CSV |
| `gherkin` | 现有 |
| `json` | 现有 |
| `xlsx` | 现有 |
| **`testrail`** | TestRail 导入 CSV：`ID,Title,Section,Type,Priority,Preconditions,Steps,Expected,References` |
| **`xray`** | Xray CSV：`Issue Key,Summary,Description,Test Type,Steps,Expected Result,Labels,Requirement` |

- `--stack` 过滤；`--out` 指定文件。
- TestRail section 默认 `<stack>/<feature>`。

### 9.8 `run`

- 读取 `.testforge/run-manifest.json`；suite 可带 `stack_id`、`pack`。
- `--stack` 过滤；`--tag` 过滤。
- 每个 suite 的 `cwd` 相对 manifest 目录；init 生成时按 stack root 计算。
- `reruns`/flaky 保持现有逻辑。
- 结果 `run-results.json` 增加 `stack_id`/`pack`。

### 9.9 `gate`

- 全局阈值 + 每 stack 覆盖。
- 覆盖率解析按 `coverage.parser` 路由：
  - `coverage.py`（JSON）
  - `jacoco`（XML）
  - `lcov`（.info）
  - `cobertura`（XML）
  - `istanbul`（coverage-summary JSON）
  - `gcovr`（XML/JSON）
- 变异分按 `mutation.score_key` 读取。
- 无覆盖率/变异的 pack（k8s）跳过对应检查，并标注 `not_applicable`。
- 输出 `gate-report.json` 增加 `stacks` 分组。

### 9.10 `report`

- 按 stack 分组：套件、用例质量、覆盖率、门禁、失败、下一步。
- 跨 stack 汇总 AC 覆盖。
- 发布建议仍为 `GO/CONDITIONAL/BLOCK`。

### 9.11 `doctor`

- 检测每个 stack 的 pack 工具链：
  - Python：python/pytest/uv/coverage/mutmut
  - Java：java/mvn/gradle/docker
  - C++：cmake/ctest/compiler/gcov/lcov/gcovr/mull
  - Frontend：node/npm/npx/playwright
  - K8s：kubectl/testkube/chainsaw/helm/docker
- 输出“可用/缺失/建议安装命令”。
- 不自动安装。

### 9.12 `mcp`

- `python testforge.py mcp` 启动 stdio JSON-RPC 2.0 server。
- 工具：
  - `testforge_pack`
  - `testforge_validate`
  - `testforge_matrix`
  - `testforge_scaffold`
  - `testforge_export`
  - `testforge_run`
  - `testforge_gate`
  - `testforge_report`
- 默认只读：`run`/`gate`/`scaffold`/`export` 写入类工具需 `--allow-write` 或 `TESTFORGE_MCP_ALLOW_WRITE=1`。
- 参数与 CLI 对齐；返回 JSON 文本 + `isError`。
- 不执行任意 shell；`run` 只执行 manifest 中的命令。
- 资源：`testforge://config`、`testforge://packs`（可选）。

---

## 10. 数据契约扩展

### 10.1 `test-cases.schema.json`

新增可选字段：

```json
{
  "stack_id": "api",
  "pack": "python-service",
  "automation": {
    "framework": "pytest",
    "file": "tests/api/test_orders.py",
    "notes": "..."
  }
}
```

### 10.2 `e2e-cases.schema.json`

新增可选 `stack_id`、`pack`。

### 10.3 `run-manifest.schema.json`

suite 新增：

```json
{
  "stack_id": "api",
  "pack": "python-service",
  "coverage": { "parser": "coverage.py", "report": "coverage.json" },
  "mutation": { "tool": "mutmut", "report": "mutation-report.json", "score_key": "mutation_score" }
}
```

### 10.4 新增 `config.schema.json`

定义 `project/stacks/quality_gates/paths`；`stacks` 必填（或由旧字段合成）。

### 10.5 新增 `pack.schema.json`

定义第 8.1 节字段；校验 pack.json。

---

## 11. 场景包设计

### 11.1 `frontend-web`

**检测**：`package.json`（react/vue/svelte/vite）、`vite.config.*`、`playwright.config.*`。

**命令**：

```json
{
  "unit": "npx vitest run",
  "e2e": "npx playwright test",
  "a11y": "npx playwright test -g @a11y",
  "visual": "npx playwright test -g @visual",
  "coverage": "npx vitest run --coverage"
}
```

**覆盖解析**：`istanbul` → `coverage/coverage-summary.json`。

**模板**：

- `vitest.test.ts`（Vitest + Testing Library）
- `msw-handlers.ts`（MSW）
- `playwright.spec.ts`（角色/标签定位、web-first assertion、API seed）
- `playwright-a11y.spec.ts`（`@axe-core/playwright`）
- `playwright-visual.spec.ts`（`toHaveScreenshot` + `maxDiffPixelRatio`）
- `playwright.fixtures.ts`（auth/seed/cleanup）

**适配器**：

- Playwright Agents：`npx playwright init-agents --loop=claude`；planner/generator/healer。
- axe-core、Lost Pixel/Argos、Lighthouse CI。

**Prompt partial**：选择器优先级、禁止 sleep、视觉基线、a11y 规则、测试数据唯一性。

**CI**：Node 20，`npm ci`，Vitest，Playwright（含 a11y/visual），上传 trace/screenshot。

---

### 11.2 `python-service`

**检测**：`pyproject.toml`、`requirements.txt`、`setup.py`、`setup.cfg`。

**命令**：

```json
{
  "unit": "pytest -q",
  "api": "pytest tests/api -q",
  "coverage": "pytest --cov=src --cov-report=json:coverage.json",
  "mutation": "mutmut run"
}
```

**覆盖解析**：`coverage.py` → `coverage.json`。

**模板**：

- `conftest.py`（fixtures、临时目录、time freeze）
- `pytest_test.py`（正常/边界/异常）
- `testcontainers_test.py`（Postgres/Redis/Kafka）
- `schemathesis_test.py`（OpenAPI/GraphQL 属性测试）
- `hypothesis_test.py`（property/stateful）
- `async_test.py`（pytest-asyncio）

**适配器**：

- Qodo Cover（Python/Java/Go/JS/TS/PHP/Kotlin；C++ 非官方）
- Pynguin（SBST）
- Mutahunter（变异驱动）
- Schemathesis、Testcontainers

**Prompt partial**：mock 边界、fixture 作用域、async、Testcontainers、Hypothesis 不变量。

**CI**：Python 3.11，uv/pip，pytest + coverage，mutmut 可选。

---

### 11.3 `java-service`

**检测**：`pom.xml`、`build.gradle`、`build.gradle.kts`。

**命令**（Maven 默认，Gradle 覆盖）：

```json
{
  "unit": "mvn -q test",
  "integration": "mvn -q verify -Pintegration",
  "coverage": "mvn -q test jacoco:report",
  "mutation": "mvn -q org.pitest:pitest-maven:mutationCoverage"
}
```

**覆盖解析**：`jacoco` → `target/site/jacoco/jacoco.xml`。

**模板**：

- `JUnit5Test.java`（AssertJ、参数化、边界/异常）
- `TestcontainersTest.java`（Postgres/Kafka/Redis）
- `WireMockTest.java`（`WireMockExtension` + `@DynamicPropertySource`）
- `PactConsumerTest.java`（消费者契约）
- `RestAssuredTest.java`（API E2E + JSON Schema）
- `JqwikPropertyTest.java`（property-based；注意 Anti-AI clause）
- `JazzerFuzzTest.java`（coverage-guided fuzzing）

**适配器**：

- TestAgent（FSE 2026，开源，VS Code，多 Agent）
- TestSpark 0.4.0（LLM + EvoSuite + Kex）
- PIT、jqwik、Jazzer、Testcontainers、WireMock、Pact、REST Assured

**Prompt partial**：服务分层、Testcontainers、WireMock、Pact、REST Assured、PIT/Jazzer、mock 边界。

**CI**：Java 21，Maven/Gradle，Testcontainers（Docker），JaCoCo，PIT 可选。

---

### 11.4 `cpp-cli`

**检测**：`CMakeLists.txt`、`meson.build`、`BUILD.bazel`、`*.cpp/*.cc/*.hpp`。

**命令**：

```json
{
  "configure": "cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug -DCMAKE_EXPORT_COMPILE_COMMANDS=ON",
  "build": "cmake --build build -j",
  "unit": "ctest --test-dir build --output-on-failure",
  "coverage": "cmake --build build --target coverage",
  "mutation": "mull-runner ..."
}
```

**覆盖解析**：`lcov` / `gcovr` → `coverage.info` / `coverage.xml`。

**模板**：

- `gtest_test.cpp`（GoogleTest，AAA、参数化、death test）
- `catch2_test.cpp`（Catch2 3）
- `CMakeLists.test.cmake`（`FetchContent` + `gtest_discover_tests`）
- `mull.yml`（Mull 配置）
- `fuzztest.cpp`（FuzzTest）
- `rapidcheck_test.cpp`（property-based）
- `approvaltests_test.cpp`（快照）
- `cli11_test.cpp`（CLI 参数/退出码）
- `testcontainers_native.cpp`（C++ 集成测试）

**适配器**：

- UTBotCpp（KLEE 符号执行；偏旧）
- CITYWALK / LISA（2026 研究）
- UnitTest_Generator_MCP / cpp-utgen（LLM + libclang）
- testcontainers-native（C/C++，早期）

**Prompt partial**：RAII/生命周期/UB、sanitizers、golden/approval、CLI 退出码/stdout/stderr、禁止真实网络。

**CI**：CMake + Ninja，build，ctest，ASan/UBSan，lcov/gcovr，Mull 可选。

---

### 11.5 `k8s`（surface pack）

**检测**：`Chart.yaml`、`kustomization.yaml`、`chainsaw-test.yaml`、`testworkflow.yaml`。

**命令**：

```json
{
  "e2e": "chainsaw test",
  "orchestrate": "kubectl testkube run testworkflow <name>",
  "chaos": "kubectl apply -f chaos/"
}
```

**覆盖/变异**：不适用；`gate` 跳过并标注 `not_applicable`。

**模板**：

- `chainsaw-test.yaml`（声明式 K8s E2E）
- `testkube-testworkflow.yaml`（在集群内执行 Playwright/k6/JUnit）
- `terratest_test.go`（基础设施 E2E）
- `toxiproxy.json`（网络故障）
- `tracetest.yaml`（OTel trace 断言）
- `chaos-mesh-network.yaml`（网络延迟/分区）

**适配器**：

- Testkube（OSS Agent + MCP + Agent Skills + AI test selection）
- Chainsaw（现代 K8s E2E；KUTTL 为 legacy）
- Terratest、envtest、kubetest2
- Toxiproxy、Tracetest、Chaos Mesh/LitmusChaos

**Prompt partial**：namespace 隔离、清理、等待条件、trace 断言、blast radius、禁止生产。

**CI**：kind/k3d，Testkube agent，Chainsaw，k6，Tracetest。

---

## 12. 跨栈追溯与门禁

### 12.1 追溯

- 每个用例可带 `stack_id`/`pack`。
- `matrix` 输出 AC × stack；一个 AC 可以同时被多个 stack 覆盖。
- `source_refs` 仍指向 `DOC/API/CODE/TEST` 条目；上下文条目带 `stack_id`。

### 12.2 门禁

- 全局阈值 + stack 覆盖。
- `gate-report.json`：

```json
{
  "passed": false,
  "overall": { "ac_coverage": 0.82, "duplicate_similarity": 0.3 },
  "stacks": {
    "api": { "line_coverage": 0.71, "mutation_score": 0.64, "passed": true },
    "web": { "line_coverage": 0.55, "passed": false },
    "k8s": { "not_applicable": ["line_coverage", "mutation_score"], "passed": true }
  }
}
```

- `cases_min`/`flaky_rate` 可按 stack 覆盖。
- 没有覆盖率的 pack 不因缺失指标失败，但必须在报告里标注。

---

## 13. MCP / Scaffold / Export

### 13.1 MCP

- 目的：让 Claude Code/Codex/Cursor 直接调用 TestForge 的验证、矩阵、执行、门禁、报告。
- 传输：stdio；JSON-RPC 2.0；`initialize`、`tools/list`、`tools/call`。
- 工具参数与 CLI 对齐；返回 `content: [{type:"text", text: json}]`。
- 默认只读；写入工具需显式授权。
- 不与 context7/exa 等 MCP 冲突；TestForge 是独立 server。

### 13.2 Scaffold

- 确定性骨架，不调用 LLM。
- 每个 pack 提供 `scaffold` 模板：
  - Playwright：`test.fixme` + 步骤注释；
  - pytest：`@pytest.mark.skip`；
  - JUnit5：`@Disabled`；
  - GoogleTest：`DISABLED_`；
  - Chainsaw：注释 + `skip: true`。
- 输出清单，方便人工补齐。

### 13.3 Export

- TestRail/Xray CSV 列映射固定，写入 `templates/` 文档。
- 复杂步骤用编号文本：`1. ...\n   预期: ...`。
- 可选 `--split-by-stack` 生成多个文件。

---

## 14. Init UX 与向后兼容

### 14.1 示例

```bash
# 自动检测
python testforge.py init --target . --detect --with-ci

# 显式组合
python testforge.py init --target . \
  --stack frontend-web \
  --stack python-service \
  --stack java-service \
  --stack cpp-cli \
  --surface k8s \
  --with-ci

# 预置 profile
python testforge.py init --target . --profile platform
```

### 14.2 `--list-packs`

输出：

```text
frontend-web   Frontend Web (Vitest + Playwright)
python-service Python Service (pytest + Testcontainers)
java-service   Java Service (JUnit 5 + Testcontainers + PIT)
cpp-cli        C++ CLI (CMake/CTest + GoogleTest + Mull)
k8s            Kubernetes (Testkube + Chainsaw + Tracertest)
```

### 14.3 兼容

- 旧 `--profile platform/service/cli/frontend/backend` 继续可用。
- 旧配置无 `stacks` 时合成单 stack。
- 旧示例/命令不破坏。
- 新字段全部可选。

---

## 15. 交付批次与里程碑

### 批次 1（本迭代）

1. **Core 抽象**：`core/` 包、config/pack/detect、向后兼容。
2. **Packs**：`python-service`、`java-service`、`cpp-cli`。
3. **CLI**：`init --stack/--detect/--list-packs`、`scaffold`、`export testrail|xray`、`mcp`。
4. **Examples**：`examples/python-service`、`examples/java-service`、`examples/cpp-cli`。
5. **CI**：Python/Java/C++ 模板。
6. **Docs**：README、WORKFLOW、QUALITY-GATES、SECURITY、review。

### 批次 2

1. **Packs**：`frontend-web`、`k8s`。
2. **Adapters**：Playwright Agents、Testkube MCP、Chainsaw、Tracetest、TestAgent、UTBotCpp。
3. **Examples**：`examples/platform` 升级为多 stack；`examples/k8s`。
4. **Self-test**：`testforge self-test --pack ...` 跑 acceptance。

> 批次 1 不含前端/K8s 的完整模板，但 core 已支持多 stack；批次 2 只加 pack，不改 core 契约。

---

## 16. 验收标准

### 通用

- [ ] 旧配置/旧示例仍能 `validate`/`export`/`run --dry-run`。
- [ ] `init --list-packs` 列出 5 个 pack。
- [ ] `init --detect` 能从目录识别 stack 并生成配置。
- [ ] `doctor` 输出每个 stack 的工具可用性。
- [ ] `mcp` 能响应 `initialize`、`tools/list`、`tools/call`（至少 `validate`/`matrix`/`gate`/`report`）。
- [ ] 不新增强制 Python 依赖。

### 每个 pack

- [ ] `init --stack <pack> --dry-run` 输出正确配置和 manifest。
- [ ] `pack` 能收集该 stack 的文档/API/代码/测试。
- [ ] `validate` 能校验该 stack 的示例用例。
- [ ] `scaffold` 生成可编译/可跳过的骨架。
- [ ] `run --dry-run` 列出该 stack 的 suite。
- [ ] `gate` 能解析该 stack 的覆盖率/变异报告（若无则标注 not_applicable）。
- [ ] `examples/<pack>` 有 README 和可执行命令。

### 具体

- [ ] Python：`pytest`/coverage.py 解析正确；Testcontainers/Schemathesis/Hypothesis 模板可运行。
- [ ] Java：Maven/JaCoCo 解析正确；JUnit5/Testcontainers/WireMock/Pact/REST Assured 模板可编译。
- [ ] C++：CMake/CTest 命令正确；GoogleTest/Catch2 模板可编译；lcov/gcovr 解析正确。
- [ ] Frontend：Vitest/Playwright 命令正确；axe/视觉模板可运行；Playwright Agents 适配说明可执行。
- [ ] K8s：Chainsaw/Testkube 模板可 `--dry-run` 或 `kubectl apply --dry-run=client`；Toxiproxy/Tracetest 配置有 schema 示例。
- [ ] Export：TestRail/Xray CSV 列名与官方导入格式一致。

---

## 17. 风险与缓解

| 风险 | 缓解 |
|---|---|
| 检测误判（多语言 monorepo） | `--dry-run` 展示检测结果；允许 `--stack` 显式覆盖 |
| Pack 变成薄文档 | 每个 pack 必须有 acceptance；`self-test` 跑示例 |
| Core 条件分支膨胀 | pack.json 驱动；core 不 import 语言工具 |
| 覆盖率格式多样 | `coverage.parser` 路由 + 每 pack 测试 |
| C++ LLM 生成不成熟 | UTBotCpp/CITYWALK 仅适配器；不承诺生成质量 |
| jqwik Anti-AI clause | 适配器明确标注，不默认启用 |
| Playwright healer 放宽断言 | 把 agent diff 当代码评审；禁止自动合并 |
| MCP 安全 | 默认只读；写入需授权；只执行 manifest 命令 |
| 跨栈配置复杂 | 默认值 + stack override；`init --detect` 生成初稿 |
| 工具链缺失 | `doctor` 提示；`run --dry-run` 可用；gate 跳过缺指标 |

---

## 18. 留给 builder 的决定

以下由实现者按项目情况决定，不需要用户逐项确认：

- `core/` 是否用包（推荐）还是单文件拆分。
- pack.json 字段的最终命名（按本设计）。
- Python 默认包管理器：uv（fallback pip）。
- Java 默认构建：Maven（Gradle 通过检测/覆盖）。
- C++ 默认标准：C++20（可通过 CMake 覆盖）。
- 前端默认：React + Vite + Vitest + Playwright（Vue/Svelte 通过检测）。
- K8s 默认：Chainsaw 做 E2E，Testkube 做编排。
- MCP 默认只读；写入工具需 `--allow-write`。
- TestRail/Xray 列映射的细节（按官方导入模板）。
- 是否在批次 1 加 `self-test`（建议加一个最小版）。

---

## 19. 参考工具与许可证注意

| 场景 | 参考 |
|---|---|
| 前端 | Playwright Agents、Vitest、Testing Library、MSW、axe-core、Lost Pixel/Argos、Lighthouse CI |
| Python | pytest、Hypothesis、Testcontainers、Schemathesis、coverage.py、mutmut、Pynguin、Qodo Cover、Mutahunter |
| Java | JUnit 5、Testcontainers、WireMock、Pact、REST Assured、PIT、jqwik、Jazzer、TestAgent、TestSpark、EvoSuite |
| C++ | GoogleTest、Catch2、doctest、CMake/CTest、GoogleMock/Trompeloeil、FuzzTest、RapidCheck、Mull、UTBotCpp、CITYWALK、LISA、UnitTest_Generator_MCP、cpp-utgen、testcontainers-native、ApprovalTests.cpp、CLI11 |
| 集群 | Testkube、Chainsaw、KUTTL（legacy）、Terratest、envtest、kubetest2、Toxiproxy、Tracetest、Chaos Mesh、LitmusChaos |
| API | Schemathesis、Pact、oasdiff、Spectral、RESTler（次要） |

**许可证/使用注意：**

- jqwik 1.10+ 有 Anti-AI Usage Clause，AI 生成测试前确认。
- Qodo Cover 官方支持 Python/Java/Go/JS/TS/PHP/Kotlin；C++ 非官方。
- Playwright Agents 生成的测试可能使用 `page.click()`，healer 可能放宽断言；必须 review diff。
- UTBotCpp 偏旧（KLEE，Ubuntu 20.04+）；C++ LLM 生成编译成功率仍是主要风险。
- Testkube OSS Agent 为 MIT；商业 Control Plane 功能另计。
- Testcontainers-native 仍早期，需 CMake/Go/Docker 环境。

---

## 20. Builder-check 决议（2026-11-12）

独立 reviewer 读过设计后提出 9 个会影响实现计划的问题。以下 8 个由设计者裁定并写入契约；最后 1 个需要用户决定。

### 20.1 Pack 增加 `inputs`、`tools`、`scaffold`

`pack.json` 增加：

```json
{
  "inputs": {
    "docs": ["docs/**/*.md", "requirements/**/*.md"],
    "api": ["openapi.yaml", "openapi/**/*.yaml"],
    "code": ["src/**/*.py"],
    "tests": ["tests/**/*.py"]
  },
  "tools": [
    { "name": "pytest", "command": "pytest --version", "required": true, "install": "pip install pytest" },
    { "name": "coverage", "command": "coverage --version", "required": false, "install": "pip install coverage" }
  ],
  "scaffold": {
    "default_template": "pytest",
    "by_type": { "functional": "pytest", "negative": "pytest", "boundary": "pytest" }
  }
}
```

- `inputs` 由 pack 提供默认值，stack 可覆盖。
- `tools` 由 `doctor` 读取；核心不再硬编码语言工具。
- `scaffold` 指定用例类型 → 模板 id；核心只做占位符替换，不做语言判断。

### 20.2 Scaffold 契约

- 占位符固定为：`${id}`、`${title}`、`${feature}`、`${steps}`、`${expected}`、`${stack}`、`${module}`。
- 模板必须是预写的、可编译/可跳过的骨架；核心不生成语言 AST。
- 模板缺失或 pack 未声明 `scaffold`：跳过该用例并写 `scaffold-manifest.json` 的 `skipped`。
- 输出清单记录 `case_id`、`template`、`file`、`status`。

### 20.3 `run` 的 suite 类型与报告命令

- suite 增加 `kind`：`test`（默认）或 `report`。
- `init` 为 `unit/integration/api/e2e/orchestrate/chaos` 生成 `kind=test` 套件。
- `coverage`/`mutation` 生成 `kind=report` 套件，带 `run_after: ["unit","integration"]`。
- `run` 默认只跑 `kind=test`；`--with-reports` 在测试后跑 report 套件；`gate` 读取报告。
- 这样不会把 coverage/mutation 当成普通测试重复执行，也不会没有报告可用。

### 20.4 `gate` 路径与缺失语义

- 报告路径统一相对 **stack root** 解析。
- `coverage.parser` 枚举：`coverage.py|jacoco|lcov|cobertura|istanbul|gcovr|none`。
- `mutation.parser` 枚举：`json|pit-xml|stryker-json|mutmut|none`。
- `none` → `not_applicable`，不失败。
- parser 存在但报告缺失 → **默认 fail**；`--allow-missing-reports` 降级为 warning。
- JSON 用 `score_key`；PIT 解析 XML mutation score；mutmut 读取 JSON/`mutmut results` 导出。具体解析器在 pack acceptance 中验证。

### 20.5 `init` 安装与升级

- 保留现有行为：安装 `.claude/skills`、`.claude/agents`、`.claude/commands`，以及 `testforge/{core,packs,profiles,schemas,prompts,templates,adapters,ci,docs,config,README,AGENTS,LICENSE}`。
- 旧目录不删除；`--force` 只覆盖 TestForge 拥有的文件，不覆盖用户测试/配置。
- 新增 `--upgrade`：刷新 `testforge/` 但保留 `testforge.config.json` 和 `.testforge/cases`。
- 旧布局存在时，`init` 只提示，不自动删除。

### 20.6 批次 1 的 pack 范围

- 批次 1 为 `frontend-web`、`k8s` 提供 **pack.json + detect + 空模板目录 + acceptance 占位**，保证 `--list-packs` 列出 5 个 pack、`init --stack frontend-web|k8s --dry-run` 可用。
- 完整模板/acceptance 放批次 2。
- 批次 1 的完整验收只覆盖 python/java/cpp；前端/K8s 验收在批次 2 生效。

### 20.7 检测与 Monorepo

- 递归扫描 marker 文件，按“最近的包清单目录”分组：`package.json`、`pyproject.toml`、`pom.xml`/`build.gradle`、`CMakeLists.txt`、`Chart.yaml`/`kustomization.yaml`。
- 默认 stack id：`<pack>-<index>` 或目录 slug；支持 `--stack python-service:services/api` 指定 root，`--stack-id api` 指定 id。
- 同一 pack 允许多个 stack，只要 id 唯一。
- `--surface k8s` 等价于 `--stack k8s`，但标记 `kind: "surface"`。

### 20.8 旧 profile 映射

| 旧 `--profile` | 新行为 |
|---|---|
| `platform` | 检测 web + python/java + k8s；检测失败回退 `platform` 组合 |
| `service` | 检测 python/java；失败回退 `python-service` |
| `cli` | 检测 CMake；有则 `cpp-cli`，否则 `python-service` |
| `frontend` | `frontend-web` |
| `backend` | 检测 python/java；失败回退 `python-service` |

- 无 `stacks` 的旧配置：按 `project.type` + `inputs/commands` 合成单 stack，`id="default"`。
- 合成规则是确定性的：先检测，再按固定顺序回退；不随机。

### 20.9 Prompt partial 注入

- `init` 复制 `packs/<pack>/partials/*.md` 到目标 `testforge/packs/<pack>/partials/`。
- `pack` 在 `context.json`/`context.md` 中增加 `prompt_partials`（带 `stack_id`）。
- 新增 `testforge prompt --stack <id> --stage <stage> [--out <file>]`：组合 `prompts/<stage>.md` + pack partials + 当前 stack 配置，输出 Markdown。
- commands/skills 可以直接读 partials，或调用 `testforge prompt`；不再需要巨型万能 prompt。

### 20.10 唯一需要用户决定的问题

**批次 1 的范围**：

- 方案 1（推荐）：批次 1 完整做 Python/Java/C++，前端/K8s 先出 pack 骨架；批次 2 完成前端/K8s。  
- 方案 2：五个 pack 在批次 1 全部做完整模板与验收（周期更长、风险更高）。

---

## 21. 批准

请确认：

1. 是否接受“通用内核 + packs”的目录/配置/pack 契约，以及第 20 节的 8 个裁定。
2. 批次 1 选方案 1 还是方案 2。
3. 是否接受 MCP 默认只读、写入需授权。

批准后进入 `superpowers:writing-plans`，产出实现计划并按计划执行。
