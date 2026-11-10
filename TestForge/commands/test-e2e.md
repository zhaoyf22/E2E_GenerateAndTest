---
description: E2E 生成：从用户旅程生成 Gherkin/Playwright，含测试数据、断言和清理
argument-hint: "[journey/模块/base_url]"
---

# /test-e2e

用户参数：`$ARGUMENTS`

执行：

1. 读取：
   - `.testforge/cases/testable-items.json`
   - `.testforge/context/context.md`
   - `testforge.config.json` 的 `stack.frontend` / `stack.api` / `commands.e2e`
   - `testforge/prompts/03-e2e-design.md`
2. 调用 `e2e-engineer` subagent：
   - 提取 persona/主流程/替代/异常/权限；
   - 生成 `.testforge/cases/e2e-cases.json`；
   - 选择器：role/label/testid/稳定文本；
   - 测试数据：API setup 优先，唯一值，cleanup；
   - 断言：URL/可见文本/业务状态，不只元素存在。
3. 可选输出：
   - `.testforge/cases/e2e.feature`
   - `e2e/tests/generated/*.spec.ts`
4. 运行：
   ```bash
   npx playwright test
   ```
5. 失败读取 `prompts/07-repair.md`：分类 → 最小修复 → 重跑 3 次。
6. 汇报：
   - 用例数/旅程数；
   - 运行结果；
   - 失败分类；
   - 下一步：`/test-run` 或 `/test-review`。

禁止 sleep/共享状态/实现细节断言。
