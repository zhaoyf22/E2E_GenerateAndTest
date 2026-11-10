---
description: 用例设计：从可测项生成可追溯、可执行的功能/边界/异常/权限用例
argument-hint: "[模块名或 TI 范围]"
---

# /test-design

用户参数：`$ARGUMENTS`

执行：

1. 读取：
   - `.testforge/cases/testable-items.json`
   - `.testforge/context/context.md`
   - `testforge/templates/case-template.md`
   - `testforge/prompts/02-test-design.md`
2. 调用 `test-designer` subagent，逐 TI 生成：
   - 正例/负例/边界；
   - 决策表/状态迁移/权限；
   - 幂等/并发（适用时）。
3. 写入 `.testforge/cases/test-cases.json`，符合 `schemas/test-cases.schema.json`。
4. 运行：
   ```bash
   python testforge/testforge.py validate --cases .testforge/cases/test-cases.json --requirements .testforge/cases/testable-items.json
   python testforge/testforge.py matrix --cases .testforge/cases/test-cases.json --requirements .testforge/cases/testable-items.json
   ```
5. 修复 errors/warnings；合并重复。
6. 汇报：
   - 用例总数/类型/优先级/技术分布；
   - AC 覆盖；
   - 校验结果；
   - 下一步：`/test-review`。

不要为数量制造重复用例；不要写空泛步骤。
