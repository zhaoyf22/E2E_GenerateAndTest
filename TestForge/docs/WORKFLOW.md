# 工作流

## 0. 选择 pack 并安装

```bash
python TestForge/testforge.py init --list-packs
python TestForge/testforge.py init --target D:\path\to\project --profile platform --with-ci
# 或单场景
python TestForge/testforge.py init --target D:\path\to\project --stack python-service
python TestForge/testforge.py init --target D:\path\to\project --detect --dry-run
cd D:\path\to\project
python testforge/testforge.py doctor
```

## 1. 配置

编辑 `testforge.config.json`：

- `stacks[]`：每个 stack 的 `id`、`pack`、`root`；
- `stacks[].inputs.docs/api/code/tests`：该 stack 的真实路径；
- `stacks[].commands`：unit/integration/api/e2e/coverage/mutation；
- `quality_gates`：全局阈值；
- `stacks[].coverage/mutation`：报告路径与解析器。

`init` 会为每个 stack 生成 `.testforge/run-manifest.json` 的 test/report suites；`coverage`/`mutation` 默认不跑，`run --with-reports` 才跑。

## 2. 打包上下文

```bash
python testforge/testforge.py pack --with-diff
```

产物：

- `.testforge/context/context.json`
- `.testforge/context/context.md`

检查：

- 不支持的文件（PDF/DOCX 未装解析器）；
- 条目是否被截断；
- 表格/状态机是否保留。

## 3. 需求分析

```bash
# Claude Code
/test-req
```

或手动：

```bash
# 把 context.md + prompts/01-requirement-analysis.md 交给 LLM
# 保存输出为 .testforge/cases/testable-items.json
python testforge/testforge.py validate --cases .testforge/cases/testable-items.json --kind testable
```

**人工评审点 1**：确认 AC、TI、Gap List。

## 4. 用例设计

```bash
/test-design
```

或手动使用 `prompts/02-test-design.md`，保存为 `.testforge/cases/test-cases.json`。

```bash
# requirements.json 可以是单独的 AC 列表，也可以直接用 testable-items.json
python testforge/testforge.py validate --cases .testforge/cases/test-cases.json --requirements .testforge/cases/testable-items.json
python testforge/testforge.py matrix --cases .testforge/cases/test-cases.json --requirements .testforge/cases/testable-items.json
```

> `load_requirements()` 会从 `testable-items.json` 的 `requirements` 数组读取 `ac_id`，不需要额外生成 `requirements.json`。

**人工评审点 2**：P0/P1 用例、预期结果、Gap。

## 5. E2E / API / 代码

```bash
/test-e2e      # e2e-cases.json + feature/spec
/test-code     # 单元/集成测试
```

API 用例可使用 `prompts/04-api-design.md`，并可选 Schemathesis。

## 6. 评审

```bash
/test-review
```

看 `review.md` 的 verdict：

- `PASS`：进入执行；
- `REVISE`：修复阻塞项；
- `REJECT`：补材料/重做。

## 7. 执行

生成 `run-manifest.json`：

```json
{
  "suites": [
    {"name": "unit", "command": "pytest -q", "timeout": 600},
    {"name": "api", "command": "pytest tests/api -q", "timeout": 600},
    {"name": "e2e", "command": "npx playwright test", "timeout": 1800}
  ]
}
```

```bash
python testforge/testforge.py run --manifest .testforge/run-manifest.json --dry-run
python testforge/testforge.py run --manifest .testforge/run-manifest.json
```

## 8. 门禁

```bash
python testforge/testforge.py gate \
  --results .testforge/runs/run-results.json \
  --coverage coverage.json \
  --mutation mutation-report.json \
  --validation .testforge/reports/validation-report.json
```

## 9. 报告

```bash
python testforge/testforge.py report \
  --results .testforge/runs/run-results.json \
  --validation .testforge/reports/validation-report.json \
  --gate .testforge/reports/gate-report.json
```

## 10. CI

见 `ci/github-actions.yml` / `ci/gitlab-ci.yml`。把 `gate` 作为合并门禁。

## 人工评审点（不可省）

1. 需求解析后的 Gap List；
2. 用例入 TCMS 前的 P0/P1 评审；
3. 产品 bug 判定；
4. 发布建议（GO/CONDITIONAL/BLOCK）。
