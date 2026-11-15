# TestForge · Agent 使用说明

本目录是一套“从需求/设计/接口/代码生成测试用例与自动化测试”的通用套件。

## 先读

1. `docs/USAGE.md`：完整使用说明（先用第 0 节最小路径）。
2. `README.md`：能力与结构。
3. `QUICKSTART.md`：5 分钟跑通。
4. `testforge.config.json`：项目路径、技术栈、命令、门禁。
5. `prompts/00-system.md`：所有阶段的通用规则。

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

## 场景包（packs）

TestForge 现在是“通用内核 + 场景包”：

- `python-service`：pytest/coverage/Testcontainers/Schemathesis/Hypothesis
- `java-service`：Maven/JUnit 5/Testcontainers/WireMock/REST Assured/PIT
- `cpp-cli`：CMake/CTest/GoogleTest/Catch2/Mull/FuzzTest/ApprovalTests/CLI11
- `frontend-web`、`k8s`：批次 1 为骨架，批次 2 补完整模板

初始化：

```bash
python testforge/testforge.py init --list-packs
python testforge/testforge.py init --profile python-service --target .
python testforge/testforge.py init --stack python-service:services/api --stack java-service:services/order --surface k8s
python testforge/testforge.py init --detect --target .
```

新增命令：

```bash
python testforge/testforge.py scaffold --cases .testforge/cases/e2e-cases.json --stack api --out e2e/generated
python testforge/testforge.py export --cases .testforge/cases/test-cases.json --format testrail
python testforge/testforge.py export --cases .testforge/cases/test-cases.json --format xray
python testforge/testforge.py prompt --stack api --stage 02-test-design
python testforge/testforge.py mcp --allow-write
```

MCP 写入授权也可用环境变量 `TESTFORGE_MCP_ALLOW_WRITE=1`。`gate` 在 MCP 中归类为只读工具，但它仍会写 `gate-report.json`；`run`/`scaffold`/`export`/`prompt`（无论是否带 `--out`）必须显式授权。

旧 `--profile platform/service/cli/frontend/backend` 仍可用，会自动映射到 pack 组合或单 stack。显式 stack 的 `gate` 默认要求 pack 声明的覆盖率/变异报告存在；用 `--allow-missing-reports` 才降级为警告，用 `--stack <id>` 只检查单个 stack。`init --with-ci` 按 stack 生成 CI，GitLab 生成的文件需要 include 到 `.gitlab-ci.yml`。
