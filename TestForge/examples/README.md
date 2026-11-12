# 示例索引

| 示例 | 类型 | 输入 | 用途 |
|---|---|---|---|
| `platform/` | 平台级（前端 + 后端 + API） | PRD + OpenAPI + 代码 | 演示完整链路：需求→用例→E2E→API |
| `python-service/` | Python 服务 | pytest + coverage | 演示 pytest 用例、边界/异常、TestRail 导出 |
| `java-service/` | Java 服务 | Maven + JUnit 5 | 演示 JUnit 5 参数化、边界/异常 |
| `cpp-cli/` | C++ CLI | CMake + GoogleTest | 演示 C++ 单测、CLI 退出码/参数 |
| `service/` | 单个后端服务 | 服务文档 + OpenAPI | 演示契约/错误码/幂等/状态 |
| `cli/` | 单个客户端工具 | CLI 规范 | 演示退出码/stderr/文件覆盖 |

## 每个示例都有

- `requirements/`：需求/设计文档
- `requirements.json`：AC 列表（供 `validate/matrix` 使用）
- `test-cases.sample.json`：符合 `schemas/test-cases.schema.json`
- `README.md`：跑通命令

## 建议顺序

1. `cli/`：最小，先理解 JSON 契约。
2. `service/`：理解 API/契约。
3. `platform/`：理解 E2E + 前后端 + 完整链路。

## 注意

- `python-service/` 需要 `pytest`；`java-service/` 需要 JDK 17+ 和 Maven；`cpp-cli/` 需要 CMake 3.20+、C++20 编译器和 GoogleTest。
- `platform/`、`service/`、`cli/` 是纯用例/契约示例，没有真实服务；`run` 用 `--dry-run` 验证编排。
- 把配置里的路径/命令换成你的项目后再正式跑。
