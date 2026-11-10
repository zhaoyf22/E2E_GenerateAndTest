# 07 · 失败修复 / 自愈闭环

## 输入

```text
【失败结果】
.testforge/runs/run-results.json

【用例】
.testforge/cases/test-cases.json / e2e-cases.json

【证据】
- 截图/视频/trace（E2E）
- stdout/stderr（单元/API）
- 产品日志/网络请求（如有）

【约束】
- 不修改生产代码（除非确认是产品 bug）
- 不降低断言强度来“修绿”
- 不删除失败用例来“修绿”
```

## 任务

### 阶段 1：失败分类

对每个失败，判定：

- `PRODUCT_BUG`：产品行为与需求/设计不符；
- `TEST_BUG`：用例步骤/数据/断言错误；
- `ENV_BUG`：环境、依赖、数据、权限、网络；
- `FLAKY`：非确定性（时序、并发、共享状态）；
- `SELECTOR_BROKEN`：UI 结构变化导致定位失败；
- `UNKNOWN`：证据不足，需要补日志。

### 阶段 2：最小修复

- `TEST_BUG`：只改用例，不改断言目标；说明原断言为什么错。
- `SELECTOR_BROKEN`：只改 locator；优先 role/label/testid；不改业务断言；重跑。
- `ENV_BUG`：修 fixture/seed/权限；不要在用例里硬编码绕过。
- `FLAKY`：隔离状态、固定种子、加 web-first assertion、去掉固定 sleep；连续跑 3 次验证。
- `PRODUCT_BUG`：不要改测试让它通过；输出缺陷报告（步骤、期望、实际、证据、影响）。
- `UNKNOWN`：补日志/截图/网络记录，再分类。

### 阶段 3：验证

- 重跑失败用例 + 相关回归。
- 连续 3 次通过才算稳定。
- 记录修复前后差异。

### 阶段 4：输出

- `triage`：每个失败的分类、证据、根因；
- `fixes`：修改的文件/用例/选择器；
- `rerun`：重跑结果；
- `defects`：产品缺陷列表；
- `remaining`：仍需人工处理的问题。

## 红线

- 禁止 `sleep` 加长来掩盖时序问题。
- 禁止删除/跳过失败用例。
- 禁止把 `expect` 改成 `console.log`。
- 禁止用 try/except 吞掉断言失败。
