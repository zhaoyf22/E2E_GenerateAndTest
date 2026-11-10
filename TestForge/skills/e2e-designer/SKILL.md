---
name: e2e-designer
description: 从需求/设计/用户旅程生成 E2E 用例、Gherkin 和 Playwright 测试骨架，覆盖主流程、异常、权限和测试数据准备；当用户要求"生成 E2E/端到端测试/Playwright/BDD"时使用。
---

# E2E Designer

## 何时使用

- 需要从 AC/用户旅程生成端到端用例。
- 需要 Gherkin（Feature/Scenario）或 Playwright/Cypress 骨架。
- 需要设计测试数据、API setup、清理和稳定断言。
- E2E 失败需要分类/自愈。

## 输入

- `.testforge/cases/testable-items.json`
- `.testforge/context/context.md`
- `testforge.config.json` 的 `stack.frontend` / `stack.api` / `commands.e2e`
- 运行信息：base_url、测试账号、数据策略、浏览器/设备

## 工作流

1. 读取 `prompts/03-e2e-design.md`。
2. 提取 persona、入口、主流程、替代流程、异常流程、权限分支。
3. 生成 `e2e-cases.json`：
   - `steps` 带 `action/data/expected/locator_hint`；
   - `api_setup` 优先于 UI 预置数据；
   - `cleanup` 清理测试数据；
   - `expected_result` 可观察（URL/文本/状态/API 响应）。
4. 选择器优先级：role → label → testid → 稳定文本 → CSS → 最后 XPath。
5. 输出 Gherkin（可选）和 Playwright 骨架（可选）。
6. 运行：
   ```bash
   npx playwright test
   ```
7. 失败时读取 `prompts/07-repair.md`：分类 → 最小修复 → 重跑 3 次。

## 硬性约束

- 禁止 `sleep`/固定等待；用 web-first assertion。
- 禁止共享浏览器状态/依赖执行顺序。
- 禁止用实现细节做断言。
- 禁止硬编码生产账号/密钥。
- 选择器失效只改 locator，不改业务断言。

## 输出

- `.testforge/cases/e2e-cases.json`（符合 `schemas/e2e-cases.schema.json`）
- 可选：`.testforge/cases/e2e.feature`、`e2e/tests/generated/*.spec.ts`
- 运行结果：`.testforge/runs/run-results.json`

## 参考

- `prompts/03-e2e-design.md`
- `prompts/07-repair.md`
- `schemas/e2e-cases.schema.json`
- `templates/e2e.feature`
- `templates/playwright.spec.ts`
