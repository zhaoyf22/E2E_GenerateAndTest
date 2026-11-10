---
description: 代码补测：从代码/diff/覆盖率生成可执行单测，并用覆盖率/变异闭环
argument-hint: "[文件/模块/diff]"
---

# /test-code

用户参数：`$ARGUMENTS`

执行：

1. 读取：
   - 目标代码/diff；
   - 现有测试与 fixture；
   - 覆盖率报告；
   - `testforge/prompts/05-code-tests.md`。
2. 调用 `automation-engineer`（代码模式）：
   - 分析公开行为/分支/依赖；
   - 生成 pytest/Jest/JUnit；
   - mock 外部依赖；
   - 行为断言，不测私有实现。
3. 运行：
   ```bash
   pytest -q
   # 或 npm test / mvn test
   ```
4. 覆盖率无增量的测试删除/改写。
5. 变异测试（可选）：
   ```bash
   mutmut run
   ```
   存活变异体补测试；等价变异体说明。
6. 连续跑 3 次检查 flaky。
7. 汇报：
   - 新增测试数；
   - 覆盖率增量；
   - 变异分；
   - untestable；
   - 下一步：`/test-run`。

禁止 `assert True`、复制实现、依赖顺序、改生产代码。
