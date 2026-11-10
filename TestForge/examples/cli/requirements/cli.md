# mytool CLI（节选）

## 命令

```bash
mytool convert --input <file> --format json|yaml|csv [--output <file>] [--overwrite]
```

## 规则

- `--input` 必填；文件不存在：退出码 2，stderr 输出 `INPUT_NOT_FOUND`。
- `--format` 必填，只允许 `json`、`yaml`、`csv`；非法值：退出码 2，stderr 输出 `INVALID_FORMAT`。
- 不指定 `--output`：输出到 stdout。
- 指定 `--output` 且文件已存在：默认退出码 3，stderr 输出 `OUTPUT_EXISTS`；加 `--overwrite` 才覆盖。
- 成功：退出码 0；stdout 输出转换结果或写入文件。
- 输入为空文件：退出码 4，stderr 输出 `EMPTY_INPUT`。

**AC-001**：合法输入 + 合法格式，退出码 0，输出可被对应解析器解析。

**AC-002**：缺失/非法参数，退出码 2，错误码明确。

**AC-003**：输出文件已存在且无 `--overwrite`，退出码 3，不覆盖原文件；加 `--overwrite` 后覆盖。

**AC-004**：空输入退出码 4，不产生输出文件。
