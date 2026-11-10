---
name: code-test-generator
description: 从代码/diff/覆盖率生成可执行的单元、集成和回归测试，并用覆盖率与变异测试闭环；当用户要求"补单测/提高覆盖率/写 pytest/Jest/JUnit/修复失败测试"时使用。
---

# Code Test Generator

## 何时使用

- 需要为某个文件/模块/diff 补单元或集成测试。
- 需要提高覆盖率、补边界/异常、做变异测试。
- 需要 TDD（先写失败测试）。

## 输入

- 代码文件/diff
- 现有测试与 fixture/mock 约定
- 覆盖率报告（coverage.json / jacoco.xml / lcov.info）
- 约束：语言/框架、是否允许网络/DB、是否允许改生产代码

## 工作流

1. 读取 `prompts/05-code-tests.md`。
2. 分析公开行为、分支、边界、依赖、现有风格。
3. 生成测试：
   - 正常/边界/异常；
   - 外部依赖 mock/fake；
   - 行为/契约断言；
   - 测试数据固定、可清理；
   - 不引入新依赖（除非说明）。
4. 运行：
   ```bash
   pytest -q
   # 或 npm test / mvn test
   ```
5. 看覆盖率增量；没有增量的测试删除/改写。
6. 变异测试（可选）：
   ```bash
   mutmut run
   ```
   存活变异体 → 补测试；等价变异体 → 说明。
7. 连续跑 3 次检查 flaky。
8. 输出测试文件 + cases 摘要 + 运行命令 + untestable。

## TDD 模式

- 先写失败测试，确认失败原因；
- 再写最小实现；
- 重构；
- 可用 `tdd-guard` / `Probity` 强制。

## 硬性约束

- 禁止 `assert True` / 只调用不检查。
- 禁止复制实现到测试。
- 禁止依赖顺序/共享状态。
- 禁止为了覆盖率生成无意义参数化。
- 不修改生产代码（除非明确要求）。

## 输出

- 测试文件（或 unified diff）
- `cases` 摘要（测试名/目标/技术/理由）
- 覆盖率/变异结果
- `untestable` 列表

## 参考

- `prompts/05-code-tests.md`
- `templates/pytest_test.py`
- `adapters/pytest.md`
- `adapters/mutation.md`
