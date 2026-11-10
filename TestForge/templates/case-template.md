# 测试用例模板

## 表格字段（导入 TestRail/Xray/Excel 时使用）

| 字段 | 必填 | 说明 |
|---|---|---|
| ID | 是 | `TC-<模块>-<序号>`，稳定不变 |
| Title | 是 | 一句话：条件 + 动作 + 期望 |
| AC | 是 | 关联验收标准，多个用 `;` |
| Source | 是 | 上下文条目 ID / 文档章节 / 接口路径 / 代码位置 |
| Technique | 是 | EP / BVA / DT / ST / scenario / error-guessing / permission / idempotency / concurrency / contract / property / pairwise |
| Priority | 是 | P0 / P1 / P2 / P3 |
| Type | 是 | functional / negative / boundary / permission / state / integration / contract / nonfunctional / e2e / regression |
| Preconditions | 是 | 账号、数据、状态、依赖 |
| Steps | 是 | 编号步骤，含具体值 |
| Test Data | 是 | 具体测试数据，不含真实 PII |
| Expected | 是 | 可观察、可判定 |
| Postconditions | 否 | 清理/状态恢复 |
| Automatable | 是 | true / false |
| Notes | 否 | 风险、假设、待确认 |

## JSON 示例

```json
{
  "id": "TC-ORDER-012",
  "title": "库存不足时提交订单被拒绝且不扣减库存",
  "ac_ids": ["AC-ORDER-03"],
  "ti_ids": ["TI-ORDER-STOCK-01"],
  "source_refs": ["DOC-0007", "openapi.yaml#/paths/~1orders/post"],
  "technique": "EP",
  "priority": "P0",
  "type": "negative",
  "preconditions": [
    "商品 SKU-001 库存为 1",
    "用户 buyer+001@example.com 已登录",
    "购物车中 SKU-001 数量为 2"
  ],
  "steps": [
    {"action": "调用 POST /orders 提交订单", "data": "{\"sku\":\"SKU-001\",\"qty\":2}", "expected": "返回 409，错误码 STOCK_INSUFFICIENT"},
    {"action": "查询 GET /products/SKU-001", "data": "SKU-001", "expected": "库存仍为 1"},
    {"action": "查询用户订单列表", "data": "buyer+001@example.com", "expected": "没有新订单"}
  ],
  "test_data": {"sku": "SKU-001", "qty": 2, "stock": 1},
  "expected_result": "订单创建失败，返回 409/STOCK_INSUFFICIENT，库存不变，无订单记录",
  "postconditions": ["删除测试购物车项"],
  "automatable": true,
  "notes": "需覆盖并发扣减（两个请求同时买最后 1 件）"
}
```

## 写作检查

- [ ] 标题能独立看懂
- [ ] 一条只验证一个主要目标
- [ ] 步骤有具体字段/值
- [ ] 预期可判定
- [ ] 有来源
- [ ] 没有“正常/正确/符合预期”等空话
- [ ] 测试数据可重复、可清理
