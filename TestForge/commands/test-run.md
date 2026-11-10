---
description: 执行测试、失败分类、质量门禁、生成发布报告
argument-hint: "[suite: unit|api|e2e|all]"
---

# /test-run

用户参数：`$ARGUMENTS`

执行：

1. 读取 `testforge.config.json` 的 `commands`。
2. 生成/确认 `.testforge/run-manifest.json`：
   ```json
   {
     "suites": [
       {"name": "unit", "command": "pytest -q", "timeout": 600},
       {"name": "api", "command": "pytest tests/api -q", "timeout": 600},
       {"name": "e2e", "command": "npx playwright test", "timeout": 1800}
     ]
   }
   ```
3. 先 dry-run：
   ```bash
   python testforge/testforge.py run --manifest .testforge/run-manifest.json --dry-run
   ```
4. 正式运行：
   ```bash
   python testforge/testforge.py run --manifest .testforge/run-manifest.json
   ```
5. 失败调用 `test-runner`：
   - 分类：PRODUCT_BUG / TEST_BUG / ENV_BUG / FLAKY / SELECTOR_BROKEN / UNKNOWN；
   - 最小修复；
   - 重跑 3 次。
6. 门禁：
   ```bash
   python testforge/testforge.py gate --results .testforge/runs/run-results.json
   ```
7. 报告：
   ```bash
   python testforge/testforge.py report --results .testforge/runs/run-results.json --validation .testforge/reports/validation-report.json --gate .testforge/reports/gate-report.json
   ```
8. 汇报：
   - 通过/失败/超时/错误；
   - 门禁结果；
   - 发布建议 GO/CONDITIONAL/BLOCK；
   - 下一步 3-5 项。

不删除/跳过失败用例；不改断言强度来修绿。
