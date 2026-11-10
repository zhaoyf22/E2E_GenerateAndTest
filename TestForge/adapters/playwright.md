# Playwright 适配

## 用途

E2E/UI 自动化。TestForge 生成 `e2e-cases.json` + Gherkin + Playwright 骨架。

## 安装

```bash
npm init playwright@latest
# 或
npm install -D @playwright/test
npx playwright install
```

## 目录建议

```text
e2e/
├── tests/
│   ├── generated/          # TestForge 生成
│   └── manual/             # 人工维护
├── fixtures/
│   ├── api.ts              # API setup/cleanup
│   └── auth.ts             # 登录态
├── playwright.config.ts
└── .env.test
```

## 约定

- 选择器：`getByRole` / `getByLabel` / `getByTestId` / 稳定文本。
- 断言：`expect(locator).toBeVisible()` / `toHaveText()` / `toHaveURL()`，使用 web-first assertion。
- 数据：`request` fixture 或 API helper 预置；每个测试唯一数据；`afterEach` 清理。
- 禁止：`waitForTimeout` / `sleep`、共享登录态导致状态污染、依赖执行顺序。
- 失败证据：`trace: 'on-first-retry'`、`screenshot: 'only-on-failure'`、`video: 'retain-on-failure'`。

## 配置片段

```ts
import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './e2e/tests',
  retries: process.env.CI ? 2 : 0,
  use: {
    baseURL: process.env.BASE_URL ?? 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
});
```

## 在 TestForge 中

```bash
python testforge/testforge.py export --cases .testforge/cases/e2e-cases.json --format gherkin
npx playwright test
python testforge/testforge.py run --manifest .testforge/run-manifest.json
```

## 自愈

- 选择器失效：只改 locator，不改业务断言。
- 页面大改：重新生成该 journey，不要全局重写。
- 连续 3 次失败：回退人工，保留 trace。
