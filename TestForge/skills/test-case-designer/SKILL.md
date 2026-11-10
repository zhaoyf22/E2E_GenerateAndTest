---
name: test-case-designer
description: 把可测项/AC 设计成可追溯、可执行、按 ISTQB 技术覆盖的高质量测试用例；当用户要求"生成测试用例/补充用例/做等价类边界值/决策表/状态迁移"时使用。
---

# Test Case Designer

## 何时使用

- 已有 `testable-items.json` 或明确的 AC，要求生成功能/验收/异常/边界用例。
- 用户要求按 EP/BVA/DT/ST/权限/幂等/并发设计用例。
- 需要导出 TestRail/Excel/Markdown/Gherkin。

## 输入

- `.testforge/cases/testable-items.json`
- `.testforge/context/context.md`
- `templates/case-template.md`
- 可选：1-2 条团队历史用例作为风格 few-shot

## 工作流

1. 读取 `prompts/02-test-design.md`。
2. 逐 TI 生成：
   - 正例、负例、边界（min-1/min/min+1/max-1/max/max+1）；
   - 决策表覆盖关键组合；
   - 状态迁移（合法/非法/回退/终态）；
   - 权限（未登录/无权限/越权/角色切换）；
   - 幂等/并发/重试/超时（适用时）。
3. 每条用例包含：`id/title/ac_ids/ti_ids/source_refs/technique/priority/type/preconditions/steps/test_data/expected_result/postconditions/automatable/notes`。
4. 生成 `coverage_matrix` 与 `self_check`。
5. 写入 `.testforge/cases/test-cases.json`，符合 `schemas/test-cases.schema.json`。
6. 运行校验：
   ```bash
   python testforge/testforge.py validate --cases .testforge/cases/test-cases.json --requirements .testforge/cases/testable-items.json
   python testforge/testforge.py matrix --cases .testforge/cases/test-cases.json --requirements .testforge/cases/testable-items.json
   ```
7. 根据校验结果修复 errors/warnings；重复用例合并。

## 硬性约束

- 一条用例只验证一个主要目标。
- 步骤必须具体到字段/值/操作；禁止“输入信息”“验证功能正常”。
- 预期结果必须可观察、可判定，且有来源。
- 未定义行为进 `gap_list`，不写进 `expected_result`。
- 不为数量制造重复用例。

## 输出

- `.testforge/cases/test-cases.json`
- `.testforge/reports/validation-report.json`
- 可选：`export --format markdown|csv|xlsx|gherkin`

## 参考

- `prompts/02-test-design.md`
- `schemas/test-cases.schema.json`
- `templates/case-template.md`
