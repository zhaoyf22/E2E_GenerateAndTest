# TestForge · 通用 AI 测试生成与自动化套件

> 站在开源生态肩膀上，把「需求文档 / 设计文档 / 接口文档 / 代码」变成**可追溯、可执行、可验证**的测试用例与自动化测试。
>
> 适用：平台级项目（前端 + 后端）、单个服务、单个客户端工具、库/SDK。  
> 宿主：Claude Code、Codex、Cursor、Gemini CLI 等支持 Agent Skills / Subagents 的编码 Agent；也可以只用其中的 Python CLI 与提示词。

---

## 0. 当前架构（2026-11-12 更新）

TestForge 现在是 **通用内核 + 可组合场景包（packs）**：

- `core/`：语言无关的配置、pack 加载、栈检测、scaffold、TestRail/Xray 导出、MCP、prompt 组合。
- `packs/`：每个场景自带 `pack.json`、模板、prompt partial、适配器、CI、acceptance。
- `profiles/`：pack 组合；`init` 可以用 `--profile`、`--stack`、`--surface`、`--detect` 装配。
- 一个 `testforge.config.json` 可以同时声明多个 stack（web / python / java / cpp / k8s）。

**批次 1 已实现：**

| Pack | 状态 |
|---|---|
| `python-service` | 完整：pytest/coverage/Testcontainers/Schemathesis/Hypothesis |
| `java-service` | 完整：JUnit 5/Testcontainers/WireMock/REST Assured/PIT/jqwik/Jazzer 适配 |
| `cpp-cli` | 完整：CMake/CTest/GoogleTest/Catch2/Mull/FuzzTest/RapidCheck/ApprovalTests/CLI11 |
| `frontend-web` | 骨架：pack 可检测/初始化；Playwright/Vitest/axe/视觉模板在批次 2 |
| `k8s` | 骨架：pack 可检测/初始化；Chainsaw/Testkube/Toxiproxy/Tracetest 模板在批次 2 |

**新增命令：**

```bash
python testforge.py init --list-packs
python testforge.py init --stack python-service --target . --dry-run
python testforge.py init --detect --target . --dry-run
python testforge.py scaffold --cases .testforge/cases/e2e-cases.json --stack api --out e2e/generated
python testforge.py export --cases .testforge/cases/test-cases.json --format testrail
python testforge.py export --cases .testforge/cases/test-cases.json --format xray
python testforge.py prompt --stack api --stage 02-test-design
python testforge.py mcp --allow-write
```

MCP 默认只读：`run`/`scaffold`/`export`/`prompt --out` 需要 `--allow-write` 或 `TESTFORGE_MCP_ALLOW_WRITE=1`。`pack`/`validate`/`gate`/`report` 归类为只读工具（不修改源码/测试文件），但仍会写 `context.json`、validation/gate/report 等运行产物；只读不等于“无文件写入”。

旧的 `--profile platform/service/cli/frontend/backend` 仍然可用，会自动映射到 pack 组合或单 stack。

---

## 1. 它解决什么问题

| 痛点 | TestForge 的做法 |
|---|---|
| 文档里的表格/状态机/字段约束被切碎 | `pack` 先生成带来源引用的结构化上下文；可选 Docling/MinerU 解析 PDF |
| 模型只写 happy path | 提示词强制点名 EP/BVA/决策表/状态迁移/权限/异常/幂等/并发 |
| 用例不可追溯 | 每条用例必须带 `source_refs` + `ac_ids`；`validate` 检查 |
| 用例很多但重复/空泛 | `validate` 做相似度去重、空泛步骤检查；`matrix` 出 AC 覆盖矩阵 |
| 生成测试不能跑/没发现力 | `run` 执行；`gate` 检查覆盖率、变异分、flaky、AC 覆盖 |
| 每个项目都要重写 prompt | 一套 prompt + skills + subagents + 配置，按项目类型切换 |
| E2E 选择器脆弱 | 提供 Playwright/BDD 模板 + 自愈/视觉工具适配建议 |

---

## 2. 套件结构

```text
TestForge/
├── testforge.py                 # CLI：init/pack/validate/matrix/scaffold/export/run/gate/report/mcp/prompt/doctor
├── core/                        # 语言无关内核（config/packs/detect/scaffold/export_formats/mcp/prompt）
├── packs/                       # 场景包：python-service / java-service / cpp-cli / frontend-web / k8s
├── profiles/                    # pack 组合：platform / python-service / java-service / cpp-cli / web
├── config/                      # 旧版单 profile 配置（向后兼容）
├── schemas/                     # testable-items / test-cases / e2e-cases / run-manifest / config / pack
├── prompts/                     # 00-system ... 08-report
├── skills/                      # 7 个 Agent Skills（需求、用例、E2E、API、代码、评审、报告）
├── agents/                      # 7 个 Subagents（orchestrator、analyst、designer、automation、e2e、reviewer、runner）
├── commands/                    # Claude Code slash commands
├── templates/                   # 通用模板
├── adapters/                    # 通用适配器说明
├── ci/                          # 通用 CI；各 pack 也有自己的 ci/
├── tests/                       # unittest 测试（含 stack / gate / report 回归）
├── examples/                    # platform / python-service / java-service / cpp-cli
└── docs/                        # 架构、工作流、质量门禁、安全、审查记录
```

---

## 3. 三种使用方式

### 方式 A：Claude Code / Codex 里直接用（推荐）

```bash
# 1) 把套件安装进你的项目
python TestForge/testforge.py init --target D:\path\to\your-project --profile platform

# 2) 编辑配置
#    your-project/testforge.config.json
#    填 docs/api/code 路径、技术栈、测试命令

# 3) 体检
cd D:\path\to\your-project
python testforge/testforge.py doctor

# 4) 打包上下文
python testforge/testforge.py pack

# 5) 在 Claude Code 中执行
/test-req            # 需求分析 → testable-items.json
/test-design         # 用例设计 → test-cases.json
/test-e2e            # E2E 设计 → e2e-cases.json + Gherkin/Playwright
/test-code           # 代码补测 → 单元/集成测试
/test-review         # 评审 + 去重 + 覆盖
/test-run            # 执行 + 门禁 + 报告
```

> 非 Claude Code 宿主（Codex/Cursor 等）：Skills 可放到 `.agents/skills/`（Agent Skills 通用路径）；`agents/` 与 `commands/` 是 Claude Code 格式，其他宿主可直接用 `prompts/` + `testforge.py`，不必转换。

### 方式 B：只用 CLI + 提示词（不依赖 Agent 宿主）

```bash
python testforge/testforge.py pack
# 把 .testforge/context/context.md + prompts/02-test-design.md 交给任意 LLM
# 把输出保存为 .testforge/cases/test-cases.json
python testforge/testforge.py validate --cases .testforge/cases/test-cases.json
python testforge/testforge.py export --cases .testforge/cases/test-cases.json --format markdown
```

### 方式 C：接入 CI

把 `ci/github-actions.yml` 复制为 `.github/workflows/testforge.yml`，修改命令即可。`gate` 会在门禁失败时返回非 0，阻断合并。

---

## 4. 场景包（packs）与 profile

| Pack | 适用 | 默认命令 | 状态 |
|---|---|---|---|
| `python-service` | Python API/服务 | pytest、coverage.py、mutmut | 完整 |
| `java-service` | Java/Spring 服务 | Maven、JaCoCo、PIT | 完整 |
| `cpp-cli` | C++ 客户端/CLI | CMake/CTest、Mull、lcov | 完整 |
| `frontend-web` | React/Vue/Svelte Web | Vitest、Playwright、axe、视觉 | 骨架（批次 2） |
| `k8s` | Kubernetes/集群 | Chainsaw、Testkube、Toxiproxy | 骨架（批次 2） |

**组合 profile**：

```bash
python testforge.py init --profile platform   # web + python + java + cpp + k8s
python testforge.py init --profile python-service
python testforge.py init --profile java-service
python testforge.py init --profile cpp-cli
python testforge.py init --profile web
```

**显式装配**：

```bash
python testforge.py init --stack python-service:services/api --stack java-service:services/order --surface k8s
python testforge.py init --stack python-service:services/api --stack java-service:services/order --stack-id api --stack-id svc
python testforge.py init --detect --target .
```

旧 profile `service/cli/frontend/backend` 仍可用：`service`/`backend` 会检测 Python/Java（无法判定时回退 Python），`cli` 检测 CMake（否则回退 Python），`frontend` 映射到 `frontend-web`；旧配置无 `stacks` 时会合成 `default` stack。

---

## 5. 核心数据契约

```text
docs/api/code ──pack──▶ context.json + context.md
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
                    export → xlsx / md / csv / feature
                              │
                    run → run-results.json
                              │
                    gate → gate-report.json
                              │
                    report → report.md
```

所有中间产物都在 `.testforge/` 下，可纳入 Git（建议只提交 `cases/`、`reports/` 和配置，忽略 `context/` 中的大文件）。

> `validate` 支持 `--kind auto|testable|test-cases|e2e`：  
> `testable-items.json` 用 `--kind testable`；普通用例用默认 `auto` 或 `--kind test-cases`；E2E 用例会自动按 `feature` 识别。

---

## 6. 设计原则

1. **先结构化，再生成。** 不把整篇 PDF 塞给模型；先抽取可测项，再设计用例。
2. **生成与验证分离。** 生成用 LLM，验证用脚本（Schema、覆盖矩阵、相似度、覆盖率、变异分）。
3. **人工评审在关键节点。** 需求理解、预期结果、P0/P1 用例必须有人签核。
4. **可追溯。** 每条用例必须能回到 AC/设计章节/代码位置。
5. **确定性优先。** 能用 OpenAPI/状态机/属性测试覆盖的，不靠模型“想”。
6. **按项目类型裁剪。** 不追求一次覆盖所有层；先打通一条最小链路。

---

## 7. 推荐的开源搭配

| 层 | 推荐 | 作用 |
|---|---|---|
| 文档解析 | Docling（MIT） | PDF/Word/表格 → 结构化 Markdown/JSON |
| 文档→用例 | Casely / TestTeller / WHartTest | 生成 + 导出 TestRail/Excel |
| 代码→单测 | Cover-Agent / AutoCover-Lite / TestSpark | 覆盖驱动生成 |
| 变异门禁 | Mutahunter + Stryker/PIT/mutmut | 抗“假测试” |
| API/契约 | Schemathesis / Pact / RESTler | 属性/契约/状态化 |
| E2E | e2e / Midscene / Kane CLI | 自然语言 + 自愈 + 缓存 |
| 测试管理 | Kiwi TCMS + requirements / TestRail MCP | 用例库 + 追溯 |
| AI 评测 | Promptfoo / DeepEval / Ragas / Inspect AI | LLM/RAG/Agent 评测 |

详见 `docs/ADAPTERS.md` 与 `docs/ARCHITECTURE.md`。

---

## 8. 已知边界

- 本套件**不绑定模型**；你需要自备 Claude/OpenAI/本地模型或宿主 Agent。
- PDF/Word 解析质量取决于 Docling/MinerU；复杂合并单元格仍需人工校验。
- 生成的测试必须经过执行与人工评审；`gate` 只能证明“达到阈值”，不能证明“业务正确”。
- 许可证：本套件 MIT；推荐工具各自的许可证请逐项确认（尤其 AGPL、PolyForm Noncommercial、fair-source）。
- Java scaffold 模板固定使用 `com.example` 包名；TestForge 不推断 Java package，生成后需按项目调整 `package` 行和目录。
- `gate` 对显式 stack 按 pack 默认要求覆盖率/变异报告（缺失默认失败）；旧配置无 `stacks` 且未声明报告时跳过对应检查。用 `--allow-missing-reports` 可显式降级。

---

## 9. 快速开始

见 `QUICKSTART.md`（5 分钟跑通一个示例）。

## 10. 不依赖真实服务的自检

在 TestForge 根目录（PowerShell）逐条执行：

```powershell
python testforge.py --help
python testforge.py doctor --config config/testforge.config.example.json
python testforge.py validate --cases examples/platform/testable-items.sample.json --kind testable
python testforge.py validate --cases examples/platform/test-cases.sample.json --requirements examples/platform/requirements.json --out examples/platform/validation-report.json
python testforge.py matrix --cases examples/platform/test-cases.sample.json --requirements examples/platform/requirements.json --out examples/platform/coverage-matrix.json
python testforge.py export --cases examples/platform/test-cases.sample.json --format markdown --out examples/platform/test-cases.md
python testforge.py run --manifest examples/platform/run-manifest.sample.json --dry-run
```

bash/macOS 把 `python` 换成 `python3` 即可；命令本身不变。

> 如果 `validate` 报 AC 覆盖不足（示例故意留了 AC-004 未覆盖），这是预期行为，用来演示 Gap。
