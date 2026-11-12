# Platform 示例

模拟一个“前端 + 后端 + OpenAPI + 数据库”的平台项目。

## 文件

- `requirements/PRD.md`：登录、下单、权限的 AC。
- `openapi.yaml`：登录/订单/商品接口。
- `testable-items.sample.json`：AC → 可测项示例（含技术/风险/Gap）。
- `test-cases.sample.json`：4 条示例用例（功能/边界/负例/幂等）。
- `e2e-cases.sample.json`：2 条 E2E 用例。
- `run-manifest.sample.json`：unit/api/e2e 套件。

## 跑通

```bash
# 0) 从 TestForge 根目录初始化
python testforge.py init --target examples/platform --profile platform --force
cd examples/platform

# 1) 用示例配置替换
copy testforge.config.example.json testforge.config.json

# 2) 打包上下文
python ../../testforge.py pack

# 4) 校验可测项与用例
python ../../testforge.py validate --cases testable-items.sample.json --kind testable
python ../../testforge.py validate --cases test-cases.sample.json --requirements requirements.json --out .testforge/reports/validation-report.json

# 5) 生成覆盖矩阵
python ../../testforge.py matrix --cases test-cases.sample.json --requirements requirements.json --out .testforge/cases/coverage-matrix.json

# 6) 导出
python ../../testforge.py export --cases test-cases.sample.json --format markdown

# 7) dry-run 运行清单
python ../../testforge.py run --manifest run-manifest.sample.json --dry-run
```

## 注意

示例没有真实服务，`run` 的 unit/api/e2e 会失败；用 `--dry-run` 验证编排即可。把 `testforge.config.json` 的 `inputs`/`commands` 改成你的真实路径后再正式跑。
