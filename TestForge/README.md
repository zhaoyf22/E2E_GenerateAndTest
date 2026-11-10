# TestForge · 通用 AI 测试生成与自动化套件

> 站在开源生态肩膀上，把「需求文档 / 设计文档 / 接口文档 / 代码」变成**可追溯、可执行、可验证**的测试用例与自动化测试。
>
> 适用：平台级项目（前端 + 后端）、单个服务、单个客户端工具、库/SDK。  
> 宿主：Claude Code、Codex、Cursor、Gemini CLI 等支持 Agent Skills / Subagents 的编码 Agent；也可以只用其中的 Python CLI 与提示词。

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
├── testforge.py                 # 统一 CLI：init/pack/validate/matrix/export/run/gate/report/doctor
├── config/
│   ├── testforge.config.example.json
│   └── profiles/                # platform / service / cli / frontend / backend
├── schemas/                     # testable-items / test-cases / e2e-cases / run-manifest
├── prompts/                     # 00-system ... 08-report
├── skills/                      # 7 个 Agent Skills（需求、用例、E2E、API、代码、评审、报告）
├── agents/                      # 7 个 Subagents（orchestrator、analyst、designer、automation、e2e、reviewer、runner）
├── commands/                    # Claude Code slash commands
├── templates/                   # 用例、Gherkin、Playwright、pytest、API、测试计划、缺陷
├── adapters/                    # Docling / Schemathesis / Playwright / pytest / mutation / MCP 接入说明
├── ci/                          # GitHub Actions / GitLab CI
├── examples/                    # platform / service / cli 三个示例
└── docs/                        # 架构、工作流、质量门禁、安全
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

## 4. 项目类型与 profile

| Profile | 适用 | 默认输入 | 默认命令 |
|---|---|---|---|
| `platform` | 前端 + 后端 + API + DB | docs、openapi、前端/后端代码 | unit、api、e2e |
| `service` | 单个后端服务/微服务 | docs、openapi、服务代码 | unit、api |
| `cli` | 命令行工具 | docs、CLI 代码 | unit、cli-smoke |
| `frontend` | 单页应用/客户端 | docs、前端代码 | unit、e2e |
| `backend` | 纯后端/库 | docs、代码 | unit、api |

`init --profile` 会生成对应默认配置；之后按项目实际情况改 `inputs`、`stack`、`commands` 即可。

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
