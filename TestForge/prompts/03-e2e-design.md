# 03 · E2E 设计 → e2e-cases.json + Gherkin / Playwright

## 输入

```text
【可测项】
.testforge/cases/testable-items.json

【上下文】
.testforge/context/context.md

【运行信息】
- base_url: {{http://localhost:3000}}
- 测试账号/角色: {{...}}
- 测试数据策略: {{API 创建 / 数据库 seed / UI 创建}}
- 浏览器/设备: {{Chromium / WebKit / Android / iOS}}
- 现有 E2E 框架: {{Playwright / Cypress / Selenium / Maestro}}

【输出路径】
- .testforge/cases/e2e-cases.json
- .testforge/cases/e2e.feature（可选）
- e2e/tests/generated/*.spec.ts（可选）
```

## 任务

### 阶段 1：用户旅程

- 从 AC/设计文档提取 persona、目标、入口、关键路径。
- 每个 journey 关联多个 case。
- 标出主流程、替代流程、异常流程、权限分支。

### 阶段 2：E2E 用例

每条用例必须包含：

- `id`：`E2E-<模块>-<序号>`；
- `title`：用户目标，不是“点击按钮”；
- `feature`：所属业务能力；
- `persona`：角色；
- `ac_ids` / `source_refs`；
- `priority`；
- `preconditions`：账号、数据、状态；
- `steps`：`action` + `data` + `expected` + `locator_hint`；
- `expected_result`：可观察的最终状态（页面、URL、提示、订单状态、API 响应）；
- `test_data`：唯一、可清理；
- `api_setup`：用 API 预置数据（优先于 UI 预置）；
- `cleanup`：清理步骤；
- `automatable` / `tags` / `notes`。

### 阶段 3：选择器与断言策略

优先级：

1. `getByRole` / `getByLabel` / `getByPlaceholder`；
2. `data-testid`；
3. 稳定文本；
4. CSS；
5. 最后才用 XPath。

禁止：

- `sleep(5)` / 固定等待；
- 依赖执行顺序/共享浏览器状态；
- 用实现细节（DOM 结构、内部 class）做断言；
- 一条用例验证多个无关目标；
- 硬编码生产账号/密钥。

断言优先：

- 用户可见文本/状态；
- URL/路由；
- API 响应（通过 `request` fixture 或网络拦截）；
- 业务状态（订单状态、余额、库存）；
- 不要只断言“元素存在”。

### 阶段 4：BDD 与代码

- 输出 Gherkin（Feature/Scenario/Given-When-Then），供人评审。
- 输出 Playwright 骨架（可选）：
  - 使用 `test.describe` / `test.beforeEach`；
  - 使用 `expect` 的 web-first assertion；
  - 测试数据通过 API fixture 创建；
  - 每个测试独立清理。

### 阶段 5：自愈闭环

1. 运行生成的 E2E。
2. 失败分类：产品 bug / 用例问题 / 环境问题 / 选择器失效。
3. 选择器失效：只改 locator，不改业务断言；重跑。
4. 连续 3 次仍失败：回退到人工，记录 evidence。

## 输出

严格按 `testforge/schemas/e2e-cases.schema.json` 输出 `.testforge/cases/e2e-cases.json`。

## 反模式

- 用例标题写“测试登录”，而不是“已注册用户使用正确密码登录后进入工作台”。
- 前置条件写“系统正常”，而不是“用户已注册且邮箱已验证”。
- 预期结果写“登录成功”，而不是“跳转 `/dashboard`，右上角显示用户名，返回 200”。
- 用 UI 创建大量测试数据（慢且不稳定）；优先 API setup。
- 所有用例共用同一个账号，导致状态污染。
