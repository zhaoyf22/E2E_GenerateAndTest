# Service 示例

单个后端服务：URL Shortener，含 OpenAPI 和 4 条示例用例。

## 文件

- `requirements/service.md`
- `openapi.yaml`
- `requirements.json`
- `test-cases.sample.json`

## 跑通

```bash
# 从 TestForge 根目录
python testforge.py init --target examples/service --profile service --force
cd examples/service

python ../../testforge.py pack
python ../../testforge.py validate --cases test-cases.sample.json --requirements requirements.json
python ../../testforge.py matrix --cases test-cases.sample.json --requirements requirements.json
python ../../testforge.py export --cases test-cases.sample.json --format gherkin
```

## 下一步

- 用 `prompts/04-api-design.md` 补错误码/鉴权/幂等/并发用例。
- 用 Schemathesis 对 `openapi.yaml` 做属性测试。
- 把 `testforge.config.json` 的 `commands.api` 改成你的真实命令。
