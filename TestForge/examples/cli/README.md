# CLI 示例

单个命令行工具：`mytool convert`，覆盖退出码、stderr、stdout、文件覆盖。

## 文件

- `requirements/cli.md`
- `requirements.json`
- `test-cases.sample.json`

## 跑通

```bash
# 从 TestForge 根目录
python testforge.py init --target examples/cli --profile cli --force
cd examples/cli

python ../../testforge.py pack
python ../../testforge.py validate --cases test-cases.sample.json --requirements requirements.json
python ../../testforge.py export --cases test-cases.sample.json --format markdown
```

## CLI 测试要点

- 退出码是契约：0 成功、2 参数错误、3 输出冲突、4 空输入。
- stderr 错误码要稳定、可搜索。
- stdout 不要混入日志。
- 临时目录隔离；不要污染用户目录。
- 文件覆盖/权限/编码（UTF-8）是高频缺陷。
