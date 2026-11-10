# Schemathesis 适配

## 用途

从 OpenAPI/GraphQL schema 自动生成大量输入，做属性/契约测试，覆盖边界、类型、缺失字段、非法枚举。确定性、CI 友好。

## 安装

```bash
pip install schemathesis
```

## 快速使用

```bash
# CLI
st run http://localhost:8000/openapi.json \
  --checks all \
  --hypothesis-max-examples 200

# 或指定文件
st run openapi/openapi.yaml --base-url http://localhost:8000
```

## pytest 集成

```python
import schemathesis

schema = schemathesis.openapi.from_uri("http://localhost:8000/openapi.json")

@schema.parametrize()
def test_api(case):
    case.call_and_validate()
```

## 在 TestForge 中的位置

- 在 `prompts/04-api-design.md` 生成 example-based 用例之后，用 Schemathesis 补属性/边界。
- 把结果写入 `.testforge/runs/`，由 `gate` 检查失败。
- 与 Pact（契约）、RESTler（有状态）互补，不互相替代。

## 注意

- 会产生噪声，需要 triage；不要把每个失败都当产品 bug。
- 只验证 schema 内约束；业务规则仍需 example-based 用例。
- 对写接口加限流/测试环境隔离，避免污染。
