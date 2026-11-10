---
name: test-reviewer
description: 评审测试用例的追溯性、技术覆盖、可执行性、预期依据、原子性、重复度、独立性和风险覆盖；当用户要求"评审用例/去重/覆盖率审计/发布门禁"时使用。
---

# Test Reviewer

## 何时使用

- 用例生成后、入 TCMS 前。
- 需要检查 AC 覆盖、重复、空泛步骤、臆造预期。
- 需要给发布/合并门禁提供结论。

## 输入

- 需求/AC（`testable-items.json` 或 requirements JSON）
- 用例集（`test-cases.json` / `e2e-cases.json`）
- `templates/case-template.md`
- `testforge.config.json` 的 `quality_gates`

## 工作流

1. 读取 `prompts/06-review.md`。
2. 按 10 个维度打分（0-2）：
   追溯、技术覆盖、可执行、预期依据、原子性、去重、独立性、可自动化、优先级、风险覆盖。
3. 找出：
   - `blocking_issues`：必须修复；
   - `coverage_gaps`：未覆盖 AC/技术/风险；
   - `duplicates`：相似用例与合并建议；
   - `rewritten_cases`：仅重写有问题的用例；
   - `gap_list`：需要产品/开发确认。
4. 给结论：`PASS`（≥16/20 且关键三项 ≥1）/ `REVISE` / `REJECT`。
5. 运行脚本复核：
   ```bash
   python testforge/testforge.py validate --cases .testforge/cases/test-cases.json --requirements .testforge/cases/testable-items.json --strict
   python testforge/testforge.py matrix --cases .testforge/cases/test-cases.json --requirements .testforge/cases/testable-items.json
   ```

## 硬性约束

- 每条问题必须带用例 ID 和证据。
- 不要用“建议优化”空话；给可执行修改。
- 不要为了让分数好看而放过高风险缺口。
- 材料不足直接 `REJECT`，列出需要补充的材料。

## 输出

- `.testforge/reports/review.md`
- `.testforge/reports/review.json`
- `.testforge/reports/validation-report.json`

## 参考

- `prompts/06-review.md`
- `schemas/test-cases.schema.json`
- `templates/case-template.md`
