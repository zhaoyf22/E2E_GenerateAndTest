# TestForge · Agent 使用说明

本目录是一套“从需求/设计/接口/代码生成测试用例与自动化测试”的通用套件。

## 先读

1. `README.md`：能力与结构。
2. `QUICKSTART.md`：5 分钟跑通。
3. `testforge.config.json`：项目路径、技术栈、命令、门禁。
4. `prompts/00-system.md`：所有阶段的通用规则。

## 工作流

```text
pack
  → requirement-analyzer（testable-items.json）
  → test-designer（test-cases.json）
  → e2e-engineer / automation-engineer
  → test-reviewer
  → test-runner
  → test-reporter
```

## 常用命令

```bash
python testforge/testforge.py doctor
python testforge/testforge.py pack --with-diff
python testforge/testforge.py validate --cases .testforge/cases/testable-items.json --kind testable
python testforge/testforge.py validate --cases .testforge/cases/test-cases.json --requirements .testforge/cases/testable-items.json
python testforge/testforge.py matrix --cases .testforge/cases/test-cases.json --requirements .testforge/cases/testable-items.json
python testforge/testforge.py export --cases .testforge/cases/test-cases.json --format markdown
python testforge/testforge.py run --manifest .testforge/run-manifest.json
python testforge/testforge.py gate --results .testforge/runs/run-results.json --coverage coverage.json
python testforge/testforge.py report --results .testforge/runs/run-results.json
```

## 规则

- 只依据上下文；未定义信息进 `gap_list`。
- 每条用例带 `source_refs`。
- 一条用例一个主要目标；步骤具体；预期可判定。
- 生成与验证分离：Schema/覆盖矩阵/去重/覆盖率/变异分用脚本。
- 失败先分类，再修复；不删用例、不降断言、不用 sleep 掩盖。
- 不生成真实密钥/PII；不修改生产代码（除非明确要求）。

## 目录

- `.claude/skills/`：Agent Skills
- `.claude/agents/`：Subagents
- `.claude/commands/`：Slash commands
- `testforge/prompts/`：阶段提示词
- `testforge/schemas/`：JSON Schema
- `testforge/templates/`：用例/Playwright/pytest/API 模板
- `.testforge/`：上下文、用例、运行结果、报告

## 项目类型

`platform` / `service` / `cli` / `frontend` / `backend`，用 `--profile` 初始化。不同 profile 只改默认输入/命令/门禁，提示词和方法不变。
