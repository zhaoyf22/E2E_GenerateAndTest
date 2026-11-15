# TestForge 使用说明（全量版 + 最小路径）

> 适用版本：0.1.0（分支 `feat/testforge-universal-core-packs`，2026-11-15）
>
> 本文把「套件全量说明」和「最小使用路径」合并成一篇。第一次使用只看第 0 节；需要配置、扩展或排错时再查后面的章节。
>
> 相关文档：`README.md`（能力概览）、`QUICKSTART.md`（5 分钟示例）、`AGENTS.md`（Agent 规则）、`docs/WORKFLOW.md`（流程细节）、`docs/QUALITY-GATES.md`（门禁）、`docs/ARCHITECTURE.md`（架构）、`docs/ADAPTERS.md`（外部工具）。

---

## 0. 最小路径：一个项目，三步

适用：**单个项目、标准目录结构、使用 Claude Code**。

### 前提

- Python 3.8+。
- 不需要 `pip install`，核心 CLI 只用标准库。
- 不需要先学 profile、stack、pack。

### 第 1 步：安装进项目（每个项目一次）

```powershell
python "D:\AI世界\4.Claude世界\1.调研\1.用例生成和自动化测试\TestForge\testforge.py" init `
  --target "D:\path\to\your-project" `
  --detect --with-ci
```

- `--detect`：自动识别 Python / Java / C++ / 前端 / k8s，生成对应 `stacks`。
- `--with-ci`：顺手安装按 stack 隔离的 CI 模板。
- 想先看会写入什么，加 `--dry-run`，不会落盘。

### 第 2 步：体检

```powershell
cd "D:\path\to\your-project"
python testforge/testforge.py doctor
```

它只回答三件事：配置是否可读、Python 可选模块是否齐全、外部工具链缺什么。缺工具不影响生成用例，只影响执行对应语言的测试。

### 第 3 步：在 Claude Code 里用

用 Claude Code 打开这个项目，然后依次输入：

```text
/test-req       需求 → 可测项（testable-items.json）
/test-design    可测项 → 测试用例（test-cases.json）
/test-run       执行 + 门禁 + 报告
```

需要时再加：

```text
/test-e2e       E2E / Gherkin / Playwright
/test-code      代码补测（单元/集成）
/test-review    用例评审
```

### 最小路径完成后，你会得到

```text
your-project/
├── testforge/                  # 套件副本（CLI + packs + prompts + schemas + 模板）
├── .claude/
│   ├── skills/                 # 7 个 Skill
│   ├── agents/                 # 7 个 Subagent
│   └── commands/               # 7 个 Slash Command
├── testforge.config.json       # 自动生成的配置
├── .testforge/
│   ├── context/                # pack 产出的上下文
│   ├── cases/                  # testable-items / test-cases / e2e-cases
│   ├── runs/                   # run-results.json
│   ├── reports/                # validation / gate / review / report
│   ├── run-manifest.json       # 自动生成的 suite 清单
│   └── .gitignore              # 默认忽略 context/runs/reports
└── .github/workflows/testforge-<stack>.yml   # 可选
```

### 最小路径不需要做的事

| 内容 | 什么时候才需要 |
|---|---|
| 手写 `testforge.config.json` | 只有 `doctor` 报命令或路径不对时，改对应 stack 的 `commands` / `inputs` |
| 手动执行 `pack` / `validate` / `matrix` | 斜杠命令内部会调用；想单独检查时再用 |
| 手动执行 `gate` / `report` | `/test-run` 会调用，CI 也会调用 |
| 多 stack / `--stack-id` / `--surface` | monorepo 多语言、多个服务时 |
| MCP | 想让其他 Agent 调用 TestForge 时 |
| TestRail / Xray / Excel 导出 | 需要和 QA 平台对接时 |
| `--allow-missing-reports` 调整 | 配置好覆盖率/变异工具后，从 CI 模板中移除该参数 |

> 一句话：**90% 的时间只会用到 `init` 一次 + 三个斜杠命令。**

---

## 1. 套件是什么

TestForge 是一套「需求文档 / 设计文档 / 接口文档 / 代码 → 可追溯、可执行、可验证的测试用例与自动化测试」的工具套件。

它由三部分组成：

1. **确定性 CLI**（`testforge.py` + `core/`）：打包上下文、校验、覆盖矩阵、执行、门禁、报告、导出。只用 Python 标准库。
2. **场景包 packs**：每种技术栈的命令、模板、适配器、CI、验收标准。
3. **Agent 资产**：7 个 Skills、7 个 Subagents、7 个 Slash Commands、9 个阶段提示词，供 Claude Code 等宿主调用。

设计原则：

- 先结构化，再生成：先把文档切成可测项，不把整篇 PDF 塞给模型。
- 生成与验证分离：生成用 LLM，Schema/覆盖/去重/覆盖率/变异用脚本。
- 可追溯：每条用例带 `source_refs` 和 `ac_ids`。
- 确定性优先：能用 OpenAPI/状态机/属性测试覆盖的，不靠模型猜。
- 人工评审在关键节点：需求 Gap、P0/P1 用例、产品 bug、发布建议。
- 按项目裁剪：先打通一条最小链路，再扩展。

**它不自带模型**。你需要 Claude Code、Codex、Cursor 或其他 LLM/Agent 宿主。

---

## 2. 套件包含什么

### 2.1 规模清单

| 类别 | 数量 | 说明 |
|---|---|---|
| Python 源文件 | 8 个（约 3,750 行） | 1 个 CLI 入口 + 7 个内核模块 |
| 安装脚本 | 2 个 | `install.ps1`、`install.sh` |
| Agent Skills | 7 个 | 需求、用例、E2E、API、代码、评审、报告 |
| Subagents | 7 个 | orchestrator + 6 个专职角色 |
| Slash Commands | 7 个 | `/test-init` 等 |
| 阶段提示词 | 9 个 | `00-system` 到 `08-report` |
| JSON Schema | 6 个 | testable-items / test-cases / e2e-cases / run-manifest / config / pack |
| 场景包 | 5 个 | Python/Java/C++ 完整，前端/k8s 骨架 |
| 组合 Profile | 5 个 | platform / python-service / java-service / cpp-cli / web |
| CLI 子命令 | 12 个 | 见第 7 节 |
| MCP 工具 | 9 个 | pack/validate/matrix/gate/report/scaffold/export/run/prompt |
| 通用模板 | 7 个 | 用例、测试计划、bug 报告、Gherkin、Playwright、pytest、API |
| Pack 模板 | 17 个 | Python 5、Java 4、C++ 8 |
| 适配器说明 | 18 份 | 通用 6 + Python 3 / Java 5 / C++ 4 |
| CI 模板 | 8 个 | 通用 2 + 三个完整 pack 各 2 |
| 测试 | 18 个文件 / 75 个用例 | 75 通过，1 跳过（缺 `jsonschema`） |
| 示例 | 6 套 | platform / python-service / java-service / cpp-cli / service / cli |

### 2.2 目录结构

```text
TestForge/
├── testforge.py                 # CLI 入口
├── core/                        # 语言无关内核
│   ├── config.py                # 配置加载/合并/栈规范化
│   ├── packs.py                 # pack 加载
│   ├── detect.py                # 技术栈检测
│   ├── scaffold.py              # 测试骨架生成
│   ├── export_formats.py        # TestRail/Xray 等导出格式
│   ├── mcp.py                   # MCP stdio 服务
│   └── prompt.py                # 阶段提示词组合
├── packs/                       # 场景包
│   ├── python-service/
│   ├── java-service/
│   ├── cpp-cli/
│   ├── frontend-web/            # 骨架
│   └── k8s/                     # 骨架
├── profiles/                    # pack 组合
├── config/                      # 旧版单 profile 配置（向后兼容）
├── schemas/                     # 6 个 JSON Schema
├── prompts/                     # 9 个阶段提示词
├── skills/                      # 7 个 Agent Skill
├── agents/                      # 7 个 Subagent
├── commands/                    # 7 个 Slash Command
├── templates/                   # 通用模板
├── adapters/                    # 通用适配器说明
├── ci/                          # 通用 CI
├── tests/                       # unittest
├── examples/                    # 6 套示例
└── docs/                        # 架构/流程/门禁/安全/本说明
```

### 2.3 12 个 CLI 子命令

| 命令 | 作用 | 主要产物 |
|---|---|---|
| `init` | 安装套件、生成配置和 run manifest | `testforge/`、`.claude/`、`testforge.config.json`、`.testforge/run-manifest.json` |
| `pack` | 收集 docs/api/code/tests，切块并带来源引用 | `.testforge/context/context.json`、`context.md` |
| `validate` | 校验可测项/用例/E2E；必填、枚举、唯一 ID、相似度去重 | `validation-report.json` |
| `matrix` | 生成 AC → 用例覆盖矩阵 | `coverage-matrix.json` |
| `scaffold` | 按用例和 pack 模板生成测试骨架 | 各语言测试文件 |
| `export` | 导出 markdown/csv/gherkin/xlsx/json/testrail/xray | 对应用例文件 |
| `run` | 按 manifest 执行 suite，支持 dry-run、reruns、stack 过滤 | `.testforge/runs/run-results.json` |
| `gate` | 质量门禁：AC 覆盖、重复率、行覆盖、变异分、flaky | `gate-report.json` |
| `report` | 按 stack 汇总生成 Markdown 报告 | `report.md` |
| `mcp` | 启动 stdio MCP 服务 | MCP 协议响应 |
| `prompt` | 组合阶段提示词 + pack partial | 可交给 LLM 的 prompt |
| `doctor` | 检查 Python、配置、外部工具链 | 控制台诊断 |

### 2.4 7 个 Skills

| Skill | 作用 |
|---|---|
| `requirement-analyzer` | PRD/设计/接口 → AC、可测项、状态机、权限、边界、Gap |
| `test-case-designer` | 可测项/AC → 可追溯用例（EP/BVA/决策表/状态迁移/权限/异常/幂等/并发） |
| `e2e-designer` | 用户旅程 → E2E 用例、Gherkin、Playwright 骨架、测试数据与清理 |
| `api-test-designer` | OpenAPI/GraphQL → 契约、集成、异常、幂等、超时、并发用例 |
| `code-test-generator` | 代码/diff/覆盖率 → 单元/集成/回归测试，用覆盖率和变异闭环 |
| `test-reviewer` | 评审追溯性、技术覆盖、可执行性、原子性、重复度、风险，给 PASS/REVISE/REJECT |
| `test-reporter` | 汇总运行结果、覆盖率、变异分、flaky、门禁 → 发布报告 |

### 2.5 7 个 Subagents

| Agent | 作用 |
|---|---|
| `test-orchestrator` | 总编排：决定走需求→用例→E2E/API/代码→评审→执行→门禁→报告的哪条链路 |
| `requirement-analyst` | 需求/设计/OpenAPI → 可测项、追溯矩阵、Gap |
| `test-designer` | 可测项/AC → 功能、边界、异常、权限、幂等、并发用例 |
| `automation-engineer` | 用例/代码 → pytest/Jest/JUnit/API 测试，覆盖率与变异闭环 |
| `e2e-engineer` | 用户旅程 → Gherkin/Playwright，数据准备、稳定断言、清理 |
| `test-reviewer` | 用例评审，10 维打分，输出阻塞项与结论 |
| `test-runner` | 执行、失败分类（产品 bug/用例问题/环境问题/flaky）、最小修复 |

### 2.6 7 个 Slash Commands

| 命令 | 作用 | 主要产物 |
|---|---|---|
| `/test-init` | 检查配置、打包上下文、生成第一版可测项 | `context.md`、`testable-items.json` |
| `/test-req` | 需求分析：AC、可测项、风险、Gap | `.testforge/cases/testable-items.json` |
| `/test-design` | 用例设计：功能/边界/异常/权限 | `.testforge/cases/test-cases.json` |
| `/test-e2e` | E2E 设计：Gherkin/Playwright | `e2e-cases.json`、`.feature`、`.spec.ts` |
| `/test-code` | 代码补测：单元/集成，覆盖率/变异闭环 | 测试代码文件 |
| `/test-review` | 用例评审：追溯/覆盖/去重/风险 | `.testforge/reports/review.md` / `review.json` |
| `/test-run` | 执行 + 失败分类 + 门禁 + 报告 | `run-results.json`、`gate-report.json`、`report.md` |

### 2.7 9 个阶段提示词

```text
00-system.md                 通用规则
01-requirement-analysis.md   需求 → 可测项
02-test-design.md            可测项 → 用例
03-e2e-design.md             用户旅程 → E2E
04-api-design.md             OpenAPI → API 用例
05-code-tests.md             代码 → 单元/集成测试
06-review.md                 用例评审
07-repair.md                 失败修复
08-report.md                 测试报告
```

### 2.8 6 个 JSON Schema 与数据契约

```text
docs/api/code ──pack──▶ context.json / context.md
                              │
                              ▼
                    prompt 01 → testable-items.json
                              │
                              ▼
                    prompt 02/03/04/05 → test-cases.json / e2e-cases.json
                              │
                              ▼
                    validate → validation-report.json
                              │
                    matrix   → coverage-matrix.json
                              │
                    export   → xlsx / md / csv / feature / testrail / xray
                              │
                    run      → run-results.json
                              │
                    gate     → gate-report.json
                              │
                    report   → report.md
```

Schema 文件：`testable-items`、`test-cases`、`e2e-cases`、`run-manifest`、`config`、`pack`。

### 2.9 5 个场景包

| Pack | 适用 | 默认命令 | 状态 |
|---|---|---|---|
| `python-service` | Python API/服务 | pytest、coverage.py、mutmut | 完整 |
| `java-service` | Java/Spring 服务 | Maven、JUnit 5、JaCoCo、PIT | 完整 |
| `cpp-cli` | C++ 客户端/CLI | CMake/CTest、Mull、lcov/gcovr | 完整 |
| `frontend-web` | React/Vue/Svelte Web | Vitest、Playwright、axe、视觉 | 骨架（批次 2） |
| `k8s` | Kubernetes/集群 | Chainsaw、Testkube、Toxiproxy | 骨架（批次 2） |

每个完整 pack 自带：

- `pack.json`：检测规则、输入 glob、工具、命令、覆盖率/变异解析器、模板、scaffold 映射、prompt partial、适配器、CI、验收标准。
- `templates/`：该语言的测试模板。
- `partials/`：追加到阶段提示词的领域知识。
- `adapters/`：外部工具接入说明。
- `ci/`：GitHub Actions / GitLab CI 模板。
- `acceptance.md`：pack 的验收标准。

---

## 3. 安装范围：项目级，不是宿主级

**`init` 只对 `--target` 指定的项目生效。** 它不修改 Claude Code/Codex/Cursor 的全局配置，也不影响其他项目。

| 内容 | 安装位置 | 生效范围 |
|---|---|---|
| `testforge/` | `<项目>/testforge/` | 仅该项目 |
| `.claude/skills|agents|commands/` | `<项目>/.claude/` | 仅该项目 |
| `testforge.config.json` | `<项目>/testforge.config.json` | 仅该项目 |
| `.testforge/` | `<项目>/.testforge/` | 仅该项目 |
| CI | `<项目>/.github/` 或 `.gitlab-ci.<stack>.yml` | 仅该项目仓库 |

### 宿主差异

| 宿主 | 如何加载 |
|---|---|
| Claude Code | 自动读取当前项目的 `.claude/skills|agents|commands` |
| Codex / Cursor | 把 `skills/` 同步到 `.agents/skills/`；`agents/`、`commands/` 是 Claude Code 格式，不通用 |
| 任意模型 | 不需要安装到宿主；用 `pack` + `prompts/` + CLI |
| MCP 客户端 | 在客户端配置里注册 `testforge.py mcp`，服务以启动目录为项目根 |

### 一份工具、多个项目共用

不执行 `init`，直接拿 TestForge 源目录当共享工具箱：

```powershell
cd "D:\path\to\project-a"
python "D:\path\to\TestForge\testforge.py" pack
python "D:\path\to\TestForge\testforge.py" validate --cases .testforge/cases/test-cases.json
```

CLI 的 packs/prompts/schemas 从套件目录读取，项目路径由 `--config` 决定（默认当前目录的 `testforge.config.json`）。

代价：

- 项目里没有 `.claude/` 的 skills/commands；
- 没有自动生成的 `run-manifest.json`；
- 升级会同时影响所有项目。

### 用户级 Skills（可选）

如果希望每个项目都能用这些 Skills，可以手工把 `TestForge/skills/*` 复制/软链到用户级 `~/.claude/skills/`。`init` 不提供 `--global`，这是手工操作。

---

## 4. 三种使用方式

### 方式 A：Agent 宿主内直接用（推荐）

```powershell
python TestForge\testforge.py init --target D:\path\to\your-project --detect --with-ci
cd D:\path\to\your-project
python testforge/testforge.py doctor
```

然后在 Claude Code 中：

```text
/test-init      可选：首次体检 + 打包 + 第一版可测项
/test-req
/test-design
/test-e2e       可选
/test-code      可选
/test-review
/test-run
```

### 方式 B：只用 CLI + 提示词（不依赖 Agent 宿主）

```powershell
cd D:\path\to\your-project
python "D:\path\to\TestForge\testforge.py" pack

# 把 .testforge/context/context.md + prompts/02-test-design.md 交给任意 LLM
# 把输出保存为 .testforge/cases/test-cases.json

python "D:\path\to\TestForge\testforge.py" validate --cases .testforge/cases/test-cases.json
python "D:\path\to\TestForge\testforge.py" export --cases .testforge/cases/test-cases.json --format markdown
```

适合：已有自己的模型调用流程，只需要确定性校验和执行。

### 方式 C：接入 CI

```powershell
python TestForge\testforge.py init --target D:\path\to\your-project --detect --with-ci
```

生成规则：

- GitHub：`.github/workflows/testforge-<stack>.yml`，一个 stack 一个 workflow。
- GitLab：`.gitlab-ci.<stack>.yml`，需要在 `.gitlab-ci.yml` 中 `include`。
- 每个 job 用 `--stack <id>` 只跑本 stack 的测试和门禁。
- `gate` 失败返回非 0，阻断合并。
- 覆盖率/变异报告默认用 `--allow-missing-reports` 容忍未产生；配置好 mutmut/JaCoCo/PIT/Mull 后应移除该参数。

### 方式 D：MCP

```powershell
cd D:\path\to\your-project
python testforge/testforge.py mcp
# 写操作：
python testforge/testforge.py mcp --allow-write
```

- 默认只读：`run`、`scaffold`、`export`、`prompt` 需要 `--allow-write` 或 `TESTFORGE_MCP_ALLOW_WRITE=1`。
- `pack`、`validate`、`matrix`、`gate`、`report` 归为只读工具，但仍会写 context/validation/gate/report 等运行产物；「只读」不等于「零文件写入」。
- 服务以启动目录为项目根；多项目使用时可给工具传 `config` 参数。

---

## 5. 配置参考

配置文件：项目根目录的 `testforge.config.json`。

`init` 会自动生成。只有以下情况需要手改：

- `doctor` 报某个 stack 的命令不存在；
- 源码/文档目录不是默认布局；
- 需要调整门禁阈值；
- 需要指定覆盖率/变异报告路径。

### 5.1 多 stack 配置（推荐）

```json
{
  "project": {
    "name": "my-platform",
    "type": "platform",
    "root": "."
  },
  "stacks": [
    {
      "id": "api",
      "pack": "python-service",
      "root": "services/api"
    },
    {
      "id": "svc",
      "pack": "java-service",
      "root": "services/order"
    },
    {
      "id": "cli",
      "pack": "cpp-cli",
      "root": "tools/cli"
    },
    {
      "id": "k8s",
      "pack": "k8s",
      "root": "deploy",
      "kind": "surface"
    }
  ],
  "quality_gates": {
    "ac_coverage_min": 0.9,
    "duplicate_similarity_max": 0.85,
    "line_coverage_min": 0.6,
    "line_coverage_delta_min": 0.0,
    "mutation_score_min": 0.6,
    "flaky_rate_max": 0.02,
    "cases_min": 1
  }
}
```

### 5.2 stack 字段

| 字段 | 说明 |
|---|---|
| `id` | stack 标识；`run --stack`、CI、`by_stack` 都用它 |
| `pack` | 场景包 id：`python-service` / `java-service` / `cpp-cli` / `frontend-web` / `k8s` |
| `root` | 该 stack 相对项目根的目录 |
| `kind` | `language`（默认）或 `surface`（如 k8s） |
| `inputs` | 覆盖全局的 `docs/api/code/tests/ignore` glob，相对 `root` |
| `commands` | 覆盖 pack 默认命令 |
| `coverage` | `{ "parser": "...", "report": "..." }`，相对 `root` |
| `mutation` | `{ "tool": "...", "parser": "...", "report": "...", "score_key": "..." }` |
| `quality_gates` | 该 stack 的门禁阈值（可选） |

### 5.3 全局字段

| 字段 | 说明 |
|---|---|
| `project` | `name`、`type`、`root` |
| `inputs` | `docs`、`api`、`code`、`tests`、`ignore`；无显式 `stacks` 时生效 |
| `commands` | 无显式 `stacks` 时的 suite 命令 |
| `quality_gates` | 全局门禁阈值 |
| `generation` | `language`、`max_cases_per_ac`、`max_context_chars_per_entry`、`techniques`、`default_priority` |
| `paths` | `context`、`cases`、`runs`、`reports`、`coverage_report`、`mutation_report`、`validation_report` |
| `adapters` | 各适配器开关（docling/schemathesis/playwright/pytest/mutation/tcms） |

### 5.4 门禁阈值

| 键 | 含义 | 建议 |
|---|---|---|
| `ac_coverage_min` | 有 ≥1 条用例的 AC 占比 | ≥ 0.9 |
| `duplicate_similarity_max` | 判为重复的相似度阈值 | 0.85 |
| `line_coverage_min` | 行覆盖率下限 | 先基线，再逐步提高 |
| `line_coverage_delta_min` | 相对 baseline 的最小增量 | 0.0 |
| `mutation_score_min` | 变异分下限 | 0.6 起 |
| `flaky_rate_max` | flaky suite 占比上限 | 0.02 |
| `cases_min` | 最少用例数 | 1 |

### 5.5 旧版单 profile 配置

没有 `stacks` 的旧配置仍然可用：

- `--profile platform/service/cli/frontend/backend` 会映射到 pack 组合或单 stack；
- 旧配置会合成一个 `default` stack；
- `gate` 在旧配置且未声明报告时跳过对应检查；
- 显式 stack 默认要求 pack 声明的覆盖率/变异报告存在。

---

## 6. 标准工作流与产物

```text
init
  → doctor
  → pack
  → requirement-analyzer      testable-items.json
  → test-designer             test-cases.json
  → e2e/API/code              e2e-cases.json / 测试代码
  → test-reviewer             review.md / review.json
  → test-runner               run-results.json
  → gate                      gate-report.json
  → report                    report.md
```

### 6.1 打包上下文

```powershell
python testforge/testforge.py pack --with-diff
```

- 按 stack root 收集 docs/api/code/tests；
- 每个条目带 `source_refs` 和 `stack_id`；
- Markdown 按标题切块，代码按文件切块；
- PDF/DOCX/PPTX/XLSX 需要 Docling / pypdf / python-docx；
- 产物：`.testforge/context/context.json`、`context.md`。

### 6.2 需求分析

人工或 `/test-req` 生成 `.testforge/cases/testable-items.json`，然后：

```powershell
python testforge/testforge.py validate --cases .testforge/cases/testable-items.json --kind testable
```

**人工评审点 1**：确认 AC、可测项、Gap List。

### 6.3 用例设计

```powershell
python testforge/testforge.py validate --cases .testforge/cases/test-cases.json --requirements .testforge/cases/testable-items.json
python testforge/testforge.py matrix --cases .testforge/cases/test-cases.json --requirements .testforge/cases/testable-items.json
```

`--requirements` 可以直接用 `testable-items.json`，不需要额外造 `requirements.json`。

**人工评审点 2**：P0/P1 用例、预期结果、Gap。

### 6.4 E2E / API / 代码测试

```text
/test-e2e      → e2e-cases.json + Gherkin/Playwright
/test-code     → 单元/集成测试
```

API 用例可使用 `prompts/04-api-design.md`，可选 Schemathesis 做契约测试。

### 6.5 评审

```text
/test-review
```

看 `verdict`：

- `PASS`：进入执行；
- `REVISE`：修复阻塞项；
- `REJECT`：补材料/重做。

### 6.6 执行

`init` 会生成 `.testforge/run-manifest.json`：

```json
{
  "meta": { "project": "my-project" },
  "suites": [
    {
      "name": "api-unit",
      "command": "python -m pytest -q --ignore=testforge",
      "cwd": "..",
      "timeout": 600,
      "kind": "test",
      "stack_id": "api",
      "pack": "python-service",
      "run_after": []
    }
  ]
}
```

suite 支持字段：

| 字段 | 说明 |
|---|---|
| `name` | suite 名；report suite 的 `run_after` 引用它 |
| `command` | 执行命令 |
| `cwd` | 相对 manifest 所在目录 |
| `timeout` | 超时秒数 |
| `env` | 额外环境变量 |
| `reruns` | 重跑次数；结果不一致记为 `flaky` |
| `kind` | `test` 或 `report` |
| `stack_id` / `pack` | 归属 |
| `run_after` | report suite 的依赖 |
| `allow_failure` | 失败不阻塞 |

先 dry-run，再正式跑：

```powershell
python testforge/testforge.py run --manifest .testforge/run-manifest.json --dry-run
python testforge/testforge.py run --manifest .testforge/run-manifest.json
```

产物：`.testforge/runs/run-results.json`，含 `summary`、`by_stack`、`flaky_rate`、每个 suite 的 stdout/stderr。

### 6.7 门禁

```powershell
python testforge/testforge.py gate `
  --results .testforge/runs/run-results.json `
  --coverage coverage.json `
  --validation .testforge/reports/validation-report.json `
  --out .testforge/reports/gate-report.json
```

自动检查：AC 覆盖、重复相似度、行覆盖、行覆盖增量、变异分、flaky 率、用例数。

多 stack 语义：

- 覆盖率/变异报告相对 **stack root** 解析；
- `parser: "none"` → `not_applicable`，不失败；
- parser 存在但报告缺失 → 默认失败；`--allow-missing-reports` 降级为 warning；
- `--stack <id>` 只检查一个 stack；
- 某 stack 的 suite 失败时，该 stack 的 `passed` 为 false。

### 6.8 报告

```powershell
python testforge/testforge.py report `
  --results .testforge/runs/run-results.json `
  --validation .testforge/reports/validation-report.json `
  --gate .testforge/reports/gate-report.json `
  --out .testforge/reports/report.md
```

### 6.9 人工评审点（不可省）

1. 需求解析后的 Gap List；
2. 用例入 TCMS 前的 P0/P1 评审；
3. 产品 bug 判定；
4. 发布建议（GO / CONDITIONAL / BLOCK）。

---

## 7. 命令参考

所有命令都可以加 `--help` 查看完整参数。

### 7.1 `init`

```powershell
python testforge.py init --target . --detect --dry-run
python testforge.py init --target . --detect --with-ci
python testforge.py init --target . --profile platform
python testforge.py init --target . --stack python-service:services/api --stack java-service:services/order
python testforge.py init --target . --surface k8s:deploy
python testforge.py init --target . --upgrade
python testforge.py init --list-packs
```

| 参数 | 说明 |
|---|---|
| `--target` | 目标项目目录 |
| `--profile` | 组合 profile |
| `--stack` | pack 或 `pack:root`，可重复/逗号分隔 |
| `--stack-id` | 与 `--stack` 配对的自定义 id |
| `--surface` | 非语言 surface，如 k8s |
| `--detect` | 根据标记文件自动检测 |
| `--dry-run` | 只打印配置和 manifest，不写盘 |
| `--upgrade` | 刷新 `testforge/`，保留配置和用例 |
| `--force` | 覆盖已有配置 |
| `--with-ci` | 按 stack 安装 CI |

检测规则：根据 `detect.files`（如 `pyproject.toml`、`pom.xml`、`CMakeLists.txt`）和 `detect.globs` 找 stack root；忽略 `.git`、`node_modules`、`.venv`、`dist`、`build`、`__pycache__`、`.testforge` 等目录。

### 7.2 `pack`

```powershell
python testforge.py pack
python testforge.py pack --with-diff
python testforge.py pack --config path\to\testforge.config.json --out .testforge/context
```

### 7.3 `validate`

```powershell
python testforge.py validate --cases .testforge/cases/test-cases.json
python testforge.py validate --cases .testforge/cases/testable-items.json --kind testable
python testforge.py validate --cases .testforge/cases/test-cases.json --requirements .testforge/cases/testable-items.json --strict
python testforge.py validate --cases .testforge/cases/test-cases.json --schema testforge/schemas/test-cases.schema.json
python testforge.py validate --cases .testforge/cases/test-cases.json --stack api
```

- `--kind auto|test-cases|e2e|testable`
- `--similarity` 重复相似度阈值
- `--schema` 启用严格 JSON Schema（需 `jsonschema`）
- `--strict` 把 warning 当 error

### 7.4 `matrix`

```powershell
python testforge.py matrix --cases .testforge/cases/test-cases.json --requirements .testforge/cases/testable-items.json
python testforge.py matrix --cases .testforge/cases/test-cases.json --requirements .testforge/cases/testable-items.json --stack api
```

### 7.5 `export`

```powershell
python testforge.py export --cases .testforge/cases/test-cases.json --format markdown
python testforge.py export --cases .testforge/cases/test-cases.json --format testrail
python testforge.py export --cases .testforge/cases/test-cases.json --format xray
python testforge.py export --cases .testforge/cases/test-cases.json --format xlsx --out .testforge/reports/cases.xlsx
```

格式：`markdown`、`csv`、`gherkin`、`xlsx`、`json`、`testrail`、`xray`。

### 7.6 `scaffold`

```powershell
python testforge.py scaffold --cases .testforge/cases/test-cases.json --stack api --out tests/generated
python testforge.py scaffold --cases .testforge/cases/e2e-cases.json --stack web --force
```

按 pack 的 `scaffold.by_type` 选择模板；`--force` 覆盖已有文件。

### 7.7 `run`

```powershell
python testforge.py run --manifest .testforge/run-manifest.json --dry-run
python testforge.py run --manifest .testforge/run-manifest.json
python testforge.py run --manifest .testforge/run-manifest.json --stack api
python testforge.py run --manifest .testforge/run-manifest.json --with-reports
python testforge.py run --manifest .testforge/run-manifest.json --allow-failures
```

### 7.8 `gate`

```powershell
python testforge.py gate --results .testforge/runs/run-results.json
python testforge.py gate --results .testforge/runs/run-results.json --coverage coverage.json
python testforge.py gate --results .testforge/runs/run-results.json --stack api --allow-missing-reports
python testforge.py gate --results .testforge/runs/run-results.json --baseline 0.55
```

### 7.9 `report`

```powershell
python testforge.py report --results .testforge/runs/run-results.json
python testforge.py report --results .testforge/runs/run-results.json --validation .testforge/reports/validation-report.json --gate .testforge/reports/gate-report.json
```

### 7.10 `prompt`

```powershell
python testforge.py prompt --stack api --stage 02-test-design
python testforge.py prompt --stack api --stage 05-code-tests --out .testforge/prompts/code.md
```

`--stage` 取 `prompts/` 下的文件名（不含 `.md`）。

### 7.11 `mcp`

```powershell
python testforge.py mcp
python testforge.py mcp --allow-write
```

9 个工具：`testforge_pack`、`testforge_validate`、`testforge_matrix`、`testforge_gate`、`testforge_report`、`testforge_scaffold`、`testforge_export`、`testforge_run`、`testforge_prompt`。

### 7.12 `doctor`

```powershell
python testforge.py doctor
python testforge.py doctor --config path\to\testforge.config.json
```

输出：Python 版本、套件根、配置状态、可选 Python 模块、外部命令、每个 stack 的 pack 工具。

---

## 8. 场景包与 Profile

### 8.1 Pack 的能力

| Pack | 测试模板 | 适配器 | CI | 验收 |
|---|---|---|---|---|
| `python-service` | pytest、conftest、Testcontainers、Schemathesis、Hypothesis | qodo-cover、pynguin、mutahunter | GitHub + GitLab | 有 |
| `java-service` | JUnit 5、Testcontainers、WireMock、REST Assured | PIT、jqwik、Jazzer、TestSpark、TestAgent | GitHub + GitLab | 有 |
| `cpp-cli` | GoogleTest、Catch2、CMake、Mull、FuzzTest、RapidCheck、ApprovalTests、CLI11 | CityWalk、cpp-utgen、UTBotCpp、Testcontainers-native、unittest-generator-mcp | GitHub + GitLab | 有 |
| `frontend-web` | 批次 2 | — | 无 | 有骨架 |
| `k8s` | 批次 2 | — | 无 | 有骨架 |

### 8.2 Profiles

| Profile | 组成 |
|---|---|
| `platform` | web + api（Python）+ svc（Java）+ cli（C++）+ k8s surface |
| `python-service` | 单个 Python stack |
| `java-service` | 单个 Java stack |
| `cpp-cli` | 单个 C++ stack |
| `web` | 单个 frontend-web stack |

显式装配优先于 profile：

```powershell
python testforge.py init --target . `
  --stack python-service:services/api `
  --stack java-service:services/order `
  --stack cpp-cli:tools/cli `
  --surface k8s:deploy
```

---

## 9. 依赖

### 9.1 硬依赖

- **Python 3.8+**；
- 一个 LLM 或 Agent 宿主（Claude Code/Codex/Cursor/任意模型）。

核心 CLI 只用标准库，`pip install` 不是必需的。

### 9.2 可选 Python 依赖

`requirements-optional.txt`：

| 用途 | 包 |
|---|---|
| PDF/Word/Office 解析 | `docling`、`pypdf`、`python-docx` |
| Excel 导出 | `openpyxl` |
| 严格 JSON Schema 校验 | `jsonschema` |
| 测试执行 | `pytest`、`pytest-cov`、`pytest-xdist`、`pytest-rerunfailures`、`pytest-testmon` |
| API 属性/契约测试 | `schemathesis` |
| 变异测试 | `mutmut` |

缺失时的降级：

- PDF/DOCX 解析 → 该文件标记 unsupported；
- xlsx 导出 → 回落 CSV；
- `--schema` → 跳过严格校验并给 warning；
- 覆盖率/变异报告缺失 → `gate` 按配置失败或 warning。

### 9.3 各 Pack 的外部工具链

| Pack | 必需 | 可选 |
|---|---|---|
| `python-service` | Python、pytest | coverage、mutmut、uv |
| `java-service` | JDK、Maven | Gradle、Docker（Testcontainers） |
| `cpp-cli` | CMake、CTest、C++ 编译器 | lcov、gcovr、Mull |
| `frontend-web` | Node 18+、npm | Playwright、Vitest、axe |
| `k8s` | kubectl | Chainsaw、Testkube、Helm |

`doctor` 会逐项检查并给出安装提示。

---

## 10. 适用场景

| 场景 | 推荐配置 | 价值 |
|---|---|---|
| 平台级项目（前端+后端+集群） | `--profile platform` 或 `--detect` | 多 stack 统一用例、覆盖矩阵、门禁、报告 |
| 单个 Python/FastAPI 服务 | `--stack python-service` | 需求→API/单元测试；Schemathesis 契约；mutmut 抗假测试 |
| Java/Spring 微服务 | `--stack java-service` | JUnit 5、WireMock、Testcontainers、PIT |
| C++ 客户端/CLI 工具 | `--stack cpp-cli` | GoogleTest/Catch2、CTest、Mull、CLI11 |
| 库/SDK | 按语言选 pack | 代码驱动补测 + 覆盖率/变异闭环 |
| 文档多、测试薄弱的老项目 | `pack` + `/test-req` + `/test-design` | 从 PRD/OpenAPI 反推可测项与用例 |
| 覆盖率/质量门禁落地 | `run` + `gate` + `--with-ci` | 合并前强制 AC 覆盖、行覆盖、变异、flaky |
| QA 平台协作 | `export testrail/xray/xlsx` | 用例导入 TestRail/Xray/Excel |
| 只用 CLI、不装 Agent | 方式 B | 任意 LLM 生成，脚本做确定性校验 |

### 不适合的情况

- 前端/k8s 的完整测试生成：目前是骨架，等批次 2。
- 没有可运行测试环境却想跑 E2E：`run` 会失败，只能 `--dry-run` 验证编排。
- 期望 `gate` 证明业务正确：它只证明阈值达标，业务正确性仍需人工。
- 完全无人值守的自动修复：`test-runner` 只做分类和最小修复。

---

## 11. 常见任务配方

### 11.1 只想生成用例，不跑测试

```powershell
python testforge/testforge.py pack
# 使用 prompts/01、02 或 /test-req、/test-design
python testforge/testforge.py validate --cases .testforge/cases/test-cases.json
python testforge/testforge.py export --cases .testforge/cases/test-cases.json --format xlsx
```

### 11.2 给现有代码补单测

```text
/test-code src/your_module.py
```

或手动：

```powershell
python testforge/testforge.py pack --with-diff
# 使用 prompts/05-code-tests.md
python testforge/testforge.py scaffold --cases .testforge/cases/test-cases.json --stack api
python testforge/testforge.py run --manifest .testforge/run-manifest.json --stack api
```

### 11.3 提高覆盖率并防止假测试

1. 先跑 `coverage` 生成 `coverage.json`；
2. 再跑 `mutation` 生成变异报告；
3. `gate` 同时检查行覆盖和变异分；
4. 存活变异体补测试，等价变异体写说明。

### 11.4 接入 CI

```powershell
python testforge/testforge.py init --target . --detect --with-ci
```

- GitHub：每个 stack 一个 workflow；
- GitLab：把 `.gitlab-ci.<stack>.yml` include 进 `.gitlab-ci.yml`；
- 配置好报告工具后，移除 `--allow-missing-reports`。

### 11.5 导出到 TestRail / Xray

```powershell
python testforge/testforge.py export --cases .testforge/cases/test-cases.json --format testrail --out .testforge/reports/testrail.json
python testforge/testforge.py export --cases .testforge/cases/test-cases.json --format xray --out .testforge/reports/xray.json
```

### 11.6 monorepo 多 stack

```powershell
python testforge/testforge.py init --detect --target . --dry-run
# 检查 detect 结果，删掉误检
python testforge/testforge.py init --target . `
  --stack python-service:services/api `
  --stack java-service:services/order `
  --stack cpp-cli:tools/cli `
  --surface k8s:deploy
```

每个 stack 有独立的 `inputs`、`commands`、覆盖率/变异解析器和门禁。

### 11.7 用 MCP 给其他 Agent 调用

```powershell
cd D:\path\to\your-project
python testforge/testforge.py mcp --allow-write
```

在 MCP 客户端注册这个命令；工具调用可以传 `config` 指向其他项目。

### 11.8 升级套件

```powershell
python testforge/testforge.py init --target . --upgrade
```

刷新 `testforge/`，保留 `testforge.config.json` 和 `.testforge/cases/`。

---

## 12. 故障排查

| 现象 | 原因 | 处理 |
|---|---|---|
| `doctor` 报 pack 工具缺失 | 本机没装对应工具链 | 只影响执行；按提示安装，或先用 `--dry-run` |
| `pytest` 收集到 `testforge/templates/*_test.py` | 套件被复制进项目 | pack 默认命令已带 `--ignore=testforge`；自定义命令也要加 |
| `pytest` 命令找不到 | 脚本不在 PATH | 用 `python -m pytest` |
| `api` suite 在无 `tests/api` 时失败 | 目录不存在 | Python pack 已改为目录存在才跑；自定义命令需自行判断 |
| `gate` 报缺覆盖率/变异报告 | 显式 stack 默认要求报告 | 生成报告，或临时加 `--allow-missing-reports` |
| `--schema` 提示跳过 | 未安装 `jsonschema` | `pip install jsonschema` |
| PDF/DOCX 标记 unsupported | 未安装解析器 | `pip install docling pypdf python-docx` |
| xlsx 导出变成 CSV | 未安装 `openpyxl` | `pip install openpyxl` |
| E2E 全失败 | 没有真实服务/浏览器 | 先 `run --dry-run`；准备环境后再跑 |
| Java scaffold 包名不对 | 模板固定 `com.example` | 生成后按项目调整 `package` 和目录 |
| `.claude/` 被覆盖 | init 会覆盖同名文件 | 先备份；`init` 会打印 warning |
| GitLab CI 不生效 | 生成的是 `.gitlab-ci.<stack>.yml` | 在 `.gitlab-ci.yml` 中 include |
| PowerShell 多行命令报错 | 续行符是反引号 `` ` `` | 用单行，或确认反引号后无空格 |
| 配置文件找不到 | 相对路径按配置文件所在目录解析 | 从项目根运行，或显式传 `--config` |
| 多 stack 出现空上下文 | stack root 或 inputs 不对 | `init --dry-run` 检查 `stacks`；`pack` 后看 `unsupported` |

---

## 13. 当前状态与边界

已验证：

- 75 个 unittest 通过，1 个跳过（缺 `jsonschema`）；
- Python 示例 5 passed；
- 双 stack `pack`、legacy/显式 stack 的 `gate` 语义、`--with-ci` 按 stack 安装均已实测；
- Python 3.8 语法检查通过。

未验证：

- Java 示例 `mvn -q test`（本机无 JDK/Maven）；
- C++ 示例 CMake/CTest（本机无 CMake/g++/GoogleTest）；
- CI YAML 实际执行（本机无 PyYAML）；
- mutmut/Mull/PIT/gcovr/JaCoCo 真实运行。

已知边界：

- 套件不绑定模型，需要自备 LLM/Agent；
- PDF/Word 复杂表格仍需人工校验；
- `gate` 不能证明业务正确；
- Java scaffold 固定 `com.example`；
- 显式 stack 默认要求覆盖率/变异报告；
- `frontend-web` / `k8s` 仍是骨架，完整模板在批次 2；
- 许可证：套件 MIT；推荐工具需逐项确认（尤其 AGPL、PolyForm Noncommercial、fair-source）。

---

## 14. 速查卡

```text
# 安装（每个项目一次）
python TestForge\testforge.py init --target <项目> --detect --with-ci

# 体检
cd <项目>
python testforge/testforge.py doctor

# Claude Code
/test-req → /test-design → /test-run
可选：/test-e2e、/test-code、/test-review

# 手动链路
python testforge/testforge.py pack --with-diff
python testforge/testforge.py validate --cases .testforge/cases/test-cases.json --requirements .testforge/cases/testable-items.json
python testforge/testforge.py matrix --cases .testforge/cases/test-cases.json --requirements .testforge/cases/testable-items.json
python testforge/testforge.py export --cases .testforge/cases/test-cases.json --format markdown
python testforge/testforge.py run --manifest .testforge/run-manifest.json --dry-run
python testforge/testforge.py run --manifest .testforge/run-manifest.json
python testforge/testforge.py gate --results .testforge/runs/run-results.json
python testforge/testforge.py report --results .testforge/runs/run-results.json

# 升级
python testforge/testforge.py init --target . --upgrade
```

**只记这一句：`init` 一次，然后 `/test-req` → `/test-design` → `/test-run`。其余都是可选项。**

---

## 15. 附录：首次问答原文（套件全量清单与接入说明）

> 本节保留第一次问答的完整内容，作为「套件包含什么、各组件作用、如何接入、依赖、适用场景」的原始版本。正文第 2、4、9、10 节是同一信息的结构化版本；两者不一致时以正文为准。

### 一、套件总览

TestForge 的结构是 **通用内核 + 可组合场景包（packs）**，本身不含模型，生成依赖你选的 LLM/Agent 宿主，校验和执行靠 Python CLI。

#### 规模清单

| 类别 | 数量 | 说明 |
|---|---|---|
| Python 源文件 | **8 个**（约 3,750 行） | 1 个 CLI 入口 `testforge.py`（2,683 行）+ `core/` 7 个内核模块（config/packs/detect/scaffold/export_formats/mcp/prompt） |
| 安装脚本 | 2 个 | `install.ps1`、`install.sh` |
| Agent Skills | **7 个** | 需求、用例、E2E、API、代码、评审、报告 |
| Subagents | **7 个** | orchestrator + 6 个专职角色 |
| Slash Commands | **7 个** | `/test-init`、`/test-req`、`/test-design`、`/test-e2e`、`/test-code`、`/test-review`、`/test-run` |
| 阶段提示词 | **9 个** | `00-system` 到 `08-report` |
| JSON Schema | **6 个** | testable-items / test-cases / e2e-cases / run-manifest / config / pack |
| 场景包 Packs | **5 个** | 3 个完整（Python/Java/C++）+ 2 个骨架（前端/k8s） |
| 组合 Profile | 5 个 | platform / python-service / java-service / cpp-cli / web |
| CLI 子命令 | **12 个** | 见下表 |
| MCP 工具 | **9 个** | pack/validate/matrix/gate/report/scaffold/export/run/prompt |
| 通用模板 | 7 个 | 用例、测试计划、bug 报告、Gherkin、Playwright、pytest、API |
| Pack 模板 | 17 个 | Python 5、Java 4、C++ 8 |
| 适配器说明 | 18 份 | 通用 6 + Python 3、Java 5、C++ 4 |
| CI 模板 | 8 个 | 通用 2 + 三个完整 pack 各 2 |
| 测试 | 18 个文件 / **75 个用例** | `python -m unittest discover -s tests`：75 通过，1 跳过（缺 jsonschema） |
| 示例 | 6 套 | platform / python-service / java-service / cpp-cli / service / cli |

### 二、各组件作用

#### 1. 12 个 CLI 子命令（`testforge.py`）

| 命令 | 作用 | 产物 |
|---|---|---|
| `init` | 把套件安装进项目；支持 `--profile/--stack/--surface/--detect/--dry-run/--with-ci/--upgrade` | `testforge/`、`.claude/`、`testforge.config.json`、`.testforge/run-manifest.json` |
| `pack` | 按 stack 收集 docs/api/code/tests，切块并带来源引用 | `.testforge/context/context.json`、`context.md` |
| `validate` | 校验可测项/普通用例/E2E；必填、枚举、唯一 ID、空预期、相似度去重；可选严格 Schema | `validation-report.json` |
| `matrix` | 生成 AC → 用例覆盖矩阵，支持 `--stack` 和 `by_stack` | `coverage-matrix.json` |
| `scaffold` | 按用例和 pack 模板生成测试骨架 | 各语言的测试文件 |
| `export` | 导出 markdown/csv/gherkin/xlsx/json/**testrail/xray** | 对应用例文件 |
| `run` | 按 manifest 执行各 stack/suite，支持 `reruns` 计算 flaky、`--dry-run` | `.testforge/runs/run-results.json` |
| `gate` | 质量门禁：AC 覆盖、重复率、行覆盖、变异分、flaky；支持 `--stack` 和 `--allow-missing-reports` | `gate-report.json` |
| `report` | 按 stack 汇总生成报告 | `report.md` |
| `mcp` | 启动 stdio MCP 服务；默认只读，写操作需 `--allow-write` 或 `TESTFORGE_MCP_ALLOW_WRITE=1` | MCP 协议响应 |
| `prompt` | 把阶段提示词与 pack 的 partial 组合起来 | 可直接交给 LLM 的 prompt |
| `doctor` | 检查 Python/配置/工具链/路径 | 控制台诊断 |

#### 2. 7 个 Skills

| Skill | 作用 |
|---|---|
| `requirement-analyzer` | PRD/设计/接口 → AC、可测项、状态机、权限、边界、Gap |
| `test-case-designer` | 可测项/AC → 可追溯用例（EP/BVA/决策表/状态迁移/权限/异常/幂等/并发） |
| `e2e-designer` | 用户旅程 → E2E 用例、Gherkin、Playwright 骨架、测试数据与清理 |
| `api-test-designer` | OpenAPI/GraphQL → 契约、集成、异常、幂等、超时、并发用例 |
| `code-test-generator` | 代码/diff/覆盖率 → 单元/集成/回归测试，用覆盖率与变异闭环 |
| `test-reviewer` | 评审追溯性、技术覆盖、可执行性、原子性、重复度、风险，给 PASS/REVISE/REJECT |
| `test-reporter` | 汇总运行结果、覆盖率、变异分、flaky、门禁 → 发布报告 |

#### 3. 7 个 Subagents

`test-orchestrator`（总编排，决定走哪条链路）、`requirement-analyst`、`test-designer`、`automation-engineer`、`e2e-engineer`、`test-reviewer`、`test-runner`（执行与失败分类：产品 bug / 用例问题 / 环境问题 / flaky）。

#### 4. 5 个 Packs

| Pack | 能力 | 状态 |
|---|---|---|
| `python-service` | pytest、coverage.py、mutmut；Testcontainers/Schemathesis/Hypothesis 模板；qodo-cover/pynguin/mutahunter 适配 | 完整 |
| `java-service` | Maven、JUnit 5、Testcontainers、WireMock、REST Assured；JaCoCo/PIT；jqwik/Jazzer 适配 | 完整 |
| `cpp-cli` | CMake/CTest、GoogleTest/Catch2；Mull、lcov/gcovr；FuzzTest/RapidCheck/ApprovalTests/CLI11 | 完整 |
| `frontend-web` | 能检测、初始化，命令含 unit/e2e/a11y/visual | 骨架，Playwright/Vitest/axe 模板待批次 2 |
| `k8s` | 能检测、初始化，命令含 e2e/orchestrate/chaos | 骨架，Chainsaw/Testkube 模板待批次 2 |

每个完整 pack 自带：`pack.json` 契约、测试模板、prompt partial、适配器说明、CI 模板、验收标准（acceptance.md）、外部工具清单。

### 三、如何接入你的实际项目

#### 推荐路径（平台级项目：前端 + 后端 + 集群 + 多语言服务）

```powershell
cd "D:\AI世界\4.Claude世界\1.调研\1.用例生成和自动化测试"

# 0) 先 dry-run 看装配结果
python TestForge\testforge.py init --profile platform --target D:\path\to\your-project --dry-run

# 1) 正式安装，带按 stack 隔离的 CI
python TestForge\testforge.py init --profile platform --target D:\path\to\your-project --with-ci
```

`--profile platform` 默认装配 4 个 stack + 1 个 surface：

```text
web   frontend-web   frontend/
api   python-service services/api/
svc   java-service   services/order/
cli   cpp-cli        tools/cli/
k8s   k8s (surface)  deploy/
```

如果你的目录结构不同，改用 `--stack` 显式指定；不知道结构时先跑 `--detect --dry-run`，再删掉误检的 stack：

```powershell
python TestForge\testforge.py init --detect --target . --dry-run
python TestForge\testforge.py init `
  --stack python-service:services/api `
  --stack java-service:services/order `
  --stack cpp-cli:tools/cli `
  --surface k8s:deploy `
  --target .
```

#### `init` 会写入什么

```text
your-project/
├── testforge/                  # 套件副本（CLI + core + packs + prompts + schemas + 模板 + 文档）
├── .claude/
│   ├── skills/                 # 7 个 Skill
│   ├── agents/                 # 7 个 Subagent
│   └── commands/               # 7 个 Slash Command
├── testforge.config.json       # 项目配置：stacks / inputs / commands / quality_gates
├── .testforge/
│   ├── run-manifest.json       # 由 stacks + pack 命令自动生成
│   ├── .gitignore              # 默认忽略 context/runs/reports
│   └── context|cases|runs|reports/
└── .github/workflows/testforge-<stack>.yml   # 可选，每个 stack 一个
```

#### 安装后 5 步

1. **改配置** `testforge.config.json`：
   - `stacks[]`：每项 `id`、`pack`、`root`，可覆盖 `inputs` 和 `commands`；
   - `inputs`：docs/api/code/tests 的 glob；
   - `commands`：把 `unit/api/e2e/coverage/mutation` 换成项目真实命令；
   - `quality_gates`：AC 覆盖、重复率、行覆盖、变异分、flaky 阈值。
2. **体检**：`python testforge/testforge.py doctor`
3. **打包上下文**：`python testforge/testforge.py pack`（可加 `--with-diff` 只打包变更）
4. **生成**：
   - 在 Claude Code 里依次 `/test-req` → `/test-design` → `/test-e2e` / `/test-code` → `/test-review` → `/test-run`；
   - 或其他宿主：把 `.testforge/context/context.md` + `prompts/02-test-design.md` 交给任意 LLM，再把输出存成 `.testforge/cases/test-cases.json`。
5. **校验、执行、门禁**：

   ```bash
   python testforge/testforge.py validate --cases .testforge/cases/test-cases.json
   python testforge/testforge.py matrix --cases .testforge/cases/test-cases.json
   python testforge/testforge.py run --manifest .testforge/run-manifest.json
   python testforge/testforge.py gate --results .testforge/runs/run-results.json --coverage coverage.json
   python testforge/testforge.py report --results .testforge/runs/run-results.json
   ```

#### 其他接入方式

- **CI**：`--with-ci` 已按 stack 生成，每个 job 用 `--stack <id>` 只跑本 stack；GitLab 生成 `.gitlab-ci.<stack>.yml`，需在 `.gitlab-ci.yml` 里 `include`。模板默认带 `--allow-missing-reports`，配置好 mutmut/JaCoCo/PIT/Mull 后应移除。
- **MCP**：`python testforge/testforge.py mcp`，在 Claude Code/其他 MCP 客户端里注册；写操作需显式授权。
- **升级**：`python testforge/testforge.py init --target . --upgrade`，刷新 `testforge/`，保留配置和用例。
- **测试管理**：`export --format testrail` / `xray` / `xlsx` 交给 QA 平台。

### 四、依赖

#### 硬依赖

- **Python 3.8+**，核心 CLI 只用标准库，`pip install` 都不需要。
- 一个 **LLM 或 Agent 宿主**（Claude Code/Codex/Cursor/任意模型），套件不自带模型。

#### 可选 Python 依赖（`requirements-optional.txt`）

| 用途 | 包 |
|---|---|
| PDF/Word/Office 解析 | `docling`、`pypdf`、`python-docx` |
| Excel 导出 | `openpyxl` |
| 严格 JSON Schema 校验 | `jsonschema` |
| 测试执行 | `pytest`、`pytest-cov`、`pytest-xdist`、`pytest-rerunfailures`、`pytest-testmon` |
| API 属性/契约测试 | `schemathesis` |
| 变异测试 | `mutmut` |

缺失时的降级行为：PDF 解析报 unsupported、xlsx 回落 CSV、`--schema` 跳过严格校验并给 warning。

#### 各 Pack 的外部工具链

| Pack | 必需 | 可选 |
|---|---|---|
| python-service | Python、pytest | coverage、mutmut、uv |
| java-service | JDK、Maven | Gradle、Docker（Testcontainers） |
| cpp-cli | CMake、CTest、C++ 编译器 | lcov、gcovr、Mull |
| frontend-web | Node 18+、npm | Playwright、Vitest、axe |
| k8s | kubectl | Chainsaw、Testkube、Helm |

### 五、适用场景

| 场景 | 推荐配置 | 能解决什么 |
|---|---|---|
| 平台级项目（前端+后端+集群） | `--profile platform` 或 `--detect` | 多 stack 统一用例、覆盖矩阵、门禁与报告 |
| 单个 Python/FastAPI 服务 | `--stack python-service` | 需求→API/单元测试；Schemathesis 契约；mutmut 抗假测试 |
| Java/Spring 微服务 | `--stack java-service` | JUnit 5、WireMock、Testcontainers、PIT 变异 |
| C++ 客户端/CLI 工具 | `--stack cpp-cli` | GoogleTest/Catch2、CTest、Mull、CLI11 参数测试 |
| 库/SDK | 按语言选 pack | 代码驱动补测 + 覆盖率/变异闭环 |
| 有文档但测试薄弱的老项目 | `pack` + `/test-req`/`/test-design` | 从 PRD/OpenAPI 反推可测项与用例，先补追溯 |
| 覆盖率/质量门禁落地 | `run` + `gate` + `--with-ci` | 合并前强制 AC 覆盖、行覆盖、变异分、flaky |
| QA 平台协作 | `export testrail/xray/xlsx` | 用例导入 TestRail/Xray/Excel |
| 只想用 CLI、不装 Agent | 方式 B：CLI + prompts | 任意 LLM 生成，脚本做确定性校验 |

**不太适合的情况**：

- 前端/k8s 的完整测试生成——目前是骨架，等批次 2；
- 没有可运行测试环境却想跑 E2E——`run` 会失败，只能 `--dry-run` 验证编排；
- 期望 `gate` 证明业务正确——它只证明阈值达标，需求理解、预期结果、P0/P1 仍需人工签核；
- 完全无人值守的自动修复——`test-runner` 只做最小修复与分类，不替代人工判断。

### 六、当前验证状态

- 75 个 unittest 通过，1 个跳过（本机缺 `jsonschema`）；
- Python 示例 5 passed；双 stack `pack`、legacy/显式 stack 的 `gate` 语义均已实测；
- 未验证：Java `mvn test`、C++ CMake/CTest（本机无 JDK/Maven/CMake/g++）、CI YAML 实际执行（无 PyYAML）、mutmut/Mull/PIT/gcovr 真实运行。

> 以上状态与正文第 13 节一致；后续验证结果更新时，以第 13 节为准。
