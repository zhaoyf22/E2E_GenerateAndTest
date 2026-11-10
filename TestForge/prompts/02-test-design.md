# 02 · 测试用例设计 → test-cases.json

## 输入

```text
【可测项】
.testforge/cases/testable-items.json

【上下文】
.testforge/context/context.md

【团队用例规范】
testforge/templates/case-template.md
{{可选：粘贴 1-2 条历史用例作为风格 few-shot}}

【输出路径】
.testforge/cases/test-cases.json
```

## 任务

### 阶段 1：逐 TI 设计

对每个 `TI-xxx` 生成用例，必须满足：

- 至少 1 条正例；
- 至少 1 条负例（非法输入、越权、依赖失败、重复提交等，适用时）；
- 边界：对每个数值/长度/日期/金额/数量约束，覆盖 `min-1`、`min`、`min+1`、`max-1`、`max`、`max+1`（不适用则说明）；
- 枚举/多条件：用决策表覆盖关键规则组合，避免全排列爆炸；
- 状态机：合法迁移、非法迁移、回退、重试、超时、终态后操作；
- 权限：未登录、无权限、越权、角色切换；
- 幂等/并发：重复请求、重复消息、并发写、乐观锁冲突（适用时）；
- 接口契约：状态码、错误码、schema、必填/类型/枚举/边界。

### 阶段 2：用例字段

每条用例必须包含：

- `id`：`TC-<模块>-<序号>`；
- `title`：一句话说明“在什么条件下做什么，期望什么”；
- `ac_ids` / `ti_ids`；
- `source_refs`：上下文条目 ID 或文档章节/接口路径/代码位置；
- `technique`：EP/BVA/DT/ST/scenario/error-guessing/permission/idempotency/concurrency/contract/property/pairwise；
- `priority`：P0/P1/P2/P3；
- `type`：functional/negative/boundary/permission/state/integration/contract/nonfunctional/e2e/regression；
- `preconditions`：可执行的前置条件（数据、账号、状态）；
- `steps`：每步 `action` + `data` + `expected`；步骤要具体；
- `test_data`：具体值，不要写“合法邮箱”；
- `expected_result`：可观察、可判定；
- `postconditions`：清理/状态恢复；
- `automatable`：true/false；
- `notes`：风险、假设、待确认。

### 阶段 3：去重与自检

- 语义重复的用例合并，不要靠改标题制造“数量”。
- 每条用例只验证一个主要目标。
- 如果预期结果来自推测，删除或移入 `gap_list`。
- 输出 `coverage_matrix`：AC → 用例 ID。
- 输出 `self_check`：missing / duplicates / unexecutable / unsupported_expectations。

### 阶段 4：输出

严格按 `testforge/schemas/test-cases.schema.json` 输出，保存到 `.testforge/cases/test-cases.json`。

## 示例（节选）

```json
{
  "id": "TC-LOGIN-004",
  "title": "密码长度为 7 位时拒绝登录",
  "ac_ids": ["AC-001"],
  "ti_ids": ["TI-001-PWD-LEN"],
  "source_refs": ["DOC-0002", "requirements/PRD.md#3.1-登录"],
  "technique": "BVA",
  "priority": "P1",
  "type": "boundary",
  "preconditions": ["已存在用户 test+001@example.com，密码为 Abc12345"],
  "steps": [
    {"action": "打开登录页，输入邮箱", "data": "test+001@example.com", "expected": "邮箱输入框接受输入"},
    {"action": "输入 7 位密码并点击登录", "data": "Abc1234", "expected": "前端提示密码长度应为 8-20 位，不发送登录请求"}
  ],
  "test_data": {"email": "test+001@example.com", "password": "Abc1234"},
  "expected_result": "登录失败，提示密码长度不合法，账号未被锁定",
  "postconditions": [],
  "automatable": true,
  "notes": "边界值下界 min-1；另需覆盖 min=8、max=20、max+1=21"
}
```

## 质量红线

- 禁止“输入信息”“验证功能正常”“符合预期”等空泛表述。
- 禁止一条用例覆盖多个 AC 的多个目标。
- 禁止没有来源的预期结果。
- 禁止把实现细节（私有方法、内部字段）当断言目标。
