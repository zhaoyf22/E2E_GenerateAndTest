---
description: 用例评审：追溯/技术覆盖/可执行/去重/风险，给 PASS/REVISE/REJECT
argument-hint: "[cases 文件或模块]"
---

# /test-review

用户参数：`$ARGUMENTS`

执行：

1. 读取：
   - 需求/AC；
   - `.testforge/cases/test-cases.json` 或 `e2e-cases.json`；
   - `testforge/templates/case-template.md`；
   - `testforge/prompts/06-review.md`。
2. 调用 `test-reviewer` subagent：
   - 10 维打分（0-2）；
   - blocking_issues（带 ID/证据/建议）；
   - coverage_gaps；
   - duplicates；
   - rewritten_cases；
   - gap_list；
   - verdict。
3. 运行脚本复核：
   ```bash
   python testforge/testforge.py validate --cases .testforge/cases/test-cases.json --requirements .testforge/cases/testable-items.json --strict
   python testforge/testforge.py matrix --cases .testforge/cases/test-cases.json --requirements .testforge/cases/testable-items.json
   ```
4. 输出 `.testforge/reports/review.md` / `review.json`。
5. 汇报：
   - 分数；
   - 阻塞项；
   - 未覆盖 AC；
   - 结论；
   - 下一步：修复后 `/test-run` 或重新 `/test-design`。

不要为了让分数好看而放过高风险缺口。
