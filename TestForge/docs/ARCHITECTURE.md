# 架构

## 通用内核 + 场景包

```text
core/                  语言无关：config / packs / detect / scaffold
                       export_formats / mcp / prompt
packs/<pack>/          pack.json + templates + partials + adapters + ci + acceptance
profiles/<name>.json   stacks + surfaces 组合
testforge.config.json  stacks[]（每个 stack 一个 pack + root + commands）
```

内核不 import Java/Python/C++ 工具；pack 拥有命令、覆盖率/变异解析、模板、prompt partial、CI、验收。`init` 负责组合，`pack/validate/matrix/run/gate/report` 按 stack 工作。

## 分层

```text
0. 规范层   Spec Kit / OpenSpec / EARS / Given-When-Then
1. 知识层   Docling / MinerU / Unstructured -> context.md + source_refs
2. 生成层   requirement-analyzer -> test-designer -> e2e/api/code
3. 验证层   schema / 覆盖矩阵 / 去重 / 覆盖率 / 变异 / flaky
4. 管理层   Kiwi TCMS / TestRail / Xray / Excel
5. 运行层   pytest / Playwright / Schemathesis / Testcontainers
6. 编排层   Claude Code Skills + Subagents / LangGraph / MCP
```

## 数据流

```text
docs/api/code
   │
   ▼
pack  ──────────────▶ .testforge/context/context.json + context.md
   │
   ▼
requirement-analyzer ─▶ .testforge/cases/testable-items.json + gap_list
   │
   ▼ (人工确认 Gap)
test-designer ───────▶ .testforge/cases/test-cases.json
   │
   ├──▶ export ──────▶ xlsx / markdown / csv / feature
   │
   ▼
validate ────────────▶ .testforge/reports/validation-report.json
   │
   ├──▶ matrix ──────▶ coverage-matrix.json
   │
   ▼
e2e-engineer / automation-engineer ─▶ 可执行测试
   │
   ▼
run ─────────────────▶ .testforge/runs/run-results.json
   │
   ▼
gate ────────────────▶ .testforge/reports/gate-report.json
   │
   ▼
report ──────────────▶ .testforge/reports/report.md
```

## 目录契约

| 目录 | 作用 | 是否提交 Git |
|---|---|---|
| `.claude/skills` | Agent Skills | 是 |
| `.claude/agents` | Subagents | 是 |
| `.claude/commands` | Slash commands | 是 |
| `testforge/` | CLI + prompts + schemas + templates | 是 |
| `testforge.config.json` | 项目配置 | 是 |
| `.testforge/context/` | 上下文包（可能很大） | 建议忽略 |
| `.testforge/cases/` | 可测项/用例/矩阵 | 是（评审资产） |
| `.testforge/runs/` | 运行结果 | 忽略 |
| `.testforge/reports/` | 报告 | 可选提交摘要 |

## 设计决策

1. **单文件 CLI，stdlib only**：降低安装门槛；可选依赖（docling/openpyxl）按需启用。
2. **JSON 而非 YAML 配置**：避免 PyYAML 依赖，跨平台稳定。
3. **生成与验证分离**：LLM 负责“想”，脚本负责“查”。
4. **source_refs 贯穿始终**：上下文条目 ID 是追溯的锚点。
5. **不绑定模型/宿主**：Claude Code、Codex、Cursor 或纯 CLI 都能用。
6. **按项目类型 profile**：platform/service/cli/frontend/backend 只改配置，不改提示词。

## 扩展点

- 新语言/框架：在 `profiles/` 加 profile，或改 `commands`。
- 新工具：在 `adapters/` 加说明；在 `testforge.py` 加解析器（如新的覆盖率格式）。
- 新阶段：在 `prompts/` 加编号提示词，在 `skills/agents` 加对应角色。
- 新导出：在 `export_*` 加函数，在 `cmd_export` 注册格式。
