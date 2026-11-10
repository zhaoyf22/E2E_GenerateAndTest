---
name: api-test-designer
description: 从 OpenAPI/GraphQL/设计文档生成契约、集成、异常、幂等、超时和并发用例；当用户要求"接口测试/契约测试/API 用例/OpenAPI"时使用。
---

# API Test Designer

## 何时使用

- 有 OpenAPI/Swagger/GraphQL/proto 或设计文档。
- 需要覆盖状态码、错误码、schema、鉴权、幂等、重试、状态迁移。
- 需要 pytest/requests、Jest/supertest、JUnit/RestAssured 或 Schemathesis。

## 输入

- `openapi/**/*.yaml|json` 或设计文档
- `.testforge/context/context.md`
- `testforge.config.json` 的 `stack.api` / `commands.api`
- 鉴权方式、测试账号、依赖

## 工作流

1. 读取 `prompts/04-api-design.md`。
2. 抽取接口清单、schema、错误码、鉴权、依赖、状态机、一致性约束。
3. 生成用例：
   - 2xx 正例；
   - 每个错误码至少 1 条；
   - 缺失/多余/类型错误/越界/非法枚举；
   - 未认证/无权限/越权/token 过期；
   - 幂等：重复请求/消息/回调；
   - 超时/重试/熔断/降级/部分失败；
   - 状态机合法/非法迁移；
   - 事务回滚/补偿/最终一致/重复消费/乱序；
   - 并发写/乐观锁/库存余额。
4. 输出 `test-cases.json`（type=integration/contract/nonfunctional）。
5. 可选：
   - Schemathesis 做 schema 属性测试；
   - Pact 做消费者契约；
   - RESTler 做 staging 有状态 fuzz；
   - Testcontainers/WireMock 管依赖。
6. 运行并校验。

## 硬性约束

- 每个错误码、鉴权分支、幂等接口、状态机都要有覆盖。
- 不允许“200 即成功”；必须断言业务字段/状态。
- 不在用例里硬编码生产数据；用 fixture/seed。

## 输出

- `.testforge/cases/test-cases.json`
- 可选：API 测试代码、Schemathesis/Pact 配置

## 参考

- `prompts/04-api-design.md`
- `schemas/test-cases.schema.json`
- `templates/api_test.py`
