# 04 · 接口/设计文档 → 集成与契约用例

## 输入

```text
【设计/接口材料】
{{OpenAPI/Swagger/GraphQL schema/gRPC proto/HLD/LLD/时序图/状态机}}

【上下文】
.testforge/context/context.md

【运行信息】
- base_url: {{http://localhost:8000}}
- 鉴权方式: {{Bearer / Cookie / API Key}}
- 测试账号: {{...}}
- 依赖: {{DB / Redis / MQ / 第三方}}

【输出路径】
.testforge/cases/test-cases.json（type=integration/contract）
```

## 任务

### 阶段 1：设计要素抽取

- 接口清单：方法、路径、鉴权、请求/响应 schema、状态码、错误码。
- 依赖清单：同步/异步、超时、重试、熔断、降级、幂等键。
- 状态机：状态、事件、合法迁移、非法迁移、终态。
- 数据一致性：事务边界、最终一致、补偿、重复消费、顺序。
- 非功能：SLA、并发、容量、安全、审计、可观测性。

### 阶段 2：设计风险

- 标出未定义/矛盾的设计点（Gap List）。
- 标出高风险路径：跨服务、异步、重试、部分失败、并发写、权限边界。

### 阶段 3：用例生成

必须覆盖（适用时）：

- 契约正例：每个接口的 2xx 成功路径；
- 契约负例：每个已定义错误码至少 1 条；缺失字段、多余字段、类型错误、越界、非法枚举；
- 鉴权：未认证、无权限、越权、token 过期/刷新；
- 幂等：重复请求、重复消息、重复回调；
- 超时/重试/熔断/降级：依赖慢、依赖失败、部分成功；
- 状态机：合法迁移、非法迁移、回退、终态后操作；
- 数据一致性：事务回滚、补偿、最终一致、重复消费、乱序；
- 并发：并发写、乐观锁冲突、库存/余额扣减；
- 可观测性：关键日志/指标/追踪（如设计有要求）。

### 阶段 4：可执行断言

- 状态码、响应 schema、错误码、关键字段。
- 数据库/缓存/消息的最终状态（通过 API 或测试 fixture 查询）。
- 不要只断言“请求成功”。

### 阶段 5：工具化

- example-based：pytest + requests/httpx；Jest + supertest；JUnit + RestAssured。
- schema-based：Schemathesis（OpenAPI/GraphQL 属性测试）。
- stateful：RESTler（staging）。
- contract：Pact（消费者驱动）。
- 单元/集成：Testcontainers 起真实依赖；WireMock/Mockoon 模拟第三方。

## 输出

按 `testforge/schemas/test-cases.schema.json` 输出，`type` 使用 `integration` / `contract` / `nonfunctional`。

## 质量红线

- 每个错误码至少有 1 条用例。
- 每个鉴权分支至少有 1 条用例。
- 每个幂等接口至少有 1 条重复请求用例。
- 每个状态机至少有 1 条非法迁移用例。
- 不允许用“200 即成功”代替业务断言。
