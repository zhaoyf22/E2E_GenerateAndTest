# 5 分钟快速开始

## 前提

- Python 3.8+
- 可选：Node 18+（Playwright）、Docling（PDF 解析）、openpyxl（Excel 导出）

## 1. 安装到你的项目

```bash
# Windows PowerShell
python D:\AI世界\4.Claude世界\1.调研\1.用例生成和自动化测试\TestForge\testforge.py init `
  --target D:\path\to\your-project `
  --profile platform `
  --with-ci
```

```bash
# macOS / Linux
python /path/to/TestForge/testforge.py init --target ./your-project --profile platform --with-ci
```

## 2. 体检

```bash
cd D:\path\to\your-project
python testforge/testforge.py doctor
```

## 3. 配置

编辑 `testforge.config.json`：

```json
{
  "inputs": {
    "docs": ["docs/**/*.md", "requirements/**/*.pdf"],
    "api": ["openapi/**/*.yaml"],
    "code": ["src/**/*.py"],
    "tests": ["tests/**/*.py"]
  },
  "commands": {
    "unit": "pytest -q",
    "api": "pytest tests/api -q",
    "e2e": "npx playwright test"
  }
}
```

## 4. 打包上下文

```bash
python testforge/testforge.py pack --with-diff
```

检查 `.testforge/context/context.md`：条目是否有来源、表格是否保留、是否有 unsupported。

## 5. 生成第一版

在 Claude Code 中：

```text
/test-req
```

或手动：把 `.testforge/context/context.md` + `testforge/prompts/01-requirement-analysis.md` 交给任意 LLM，保存为 `.testforge/cases/testable-items.json`。

```bash
# 可选：校验可测项结构
python testforge/testforge.py validate --cases .testforge/cases/testable-items.json --kind testable
```

然后：

```text
/test-design
/test-review
```

## 6. 校验与导出

```bash
python testforge/testforge.py validate \
  --cases .testforge/cases/test-cases.json \
  --requirements .testforge/cases/testable-items.json \
  --schema testforge/schemas/test-cases.schema.json

python testforge/testforge.py matrix \
  --cases .testforge/cases/test-cases.json \
  --requirements .testforge/cases/testable-items.json

python testforge/testforge.py export \
  --cases .testforge/cases/test-cases.json \
  --format markdown
```

## 7. 生成 E2E / 代码测试

```text
/test-e2e
/test-code
```

## 8. 执行与门禁

```bash
python testforge/testforge.py run --manifest .testforge/run-manifest.json --dry-run
python testforge/testforge.py run --manifest .testforge/run-manifest.json
python testforge/testforge.py gate --results .testforge/runs/run-results.json --coverage coverage.json
python testforge/testforge.py report --results .testforge/runs/run-results.json
```

## 9. 用示例练手

见 `examples/platform`、`examples/service`、`examples/cli`。每个都有 README 和可直接校验的 sample JSON。

## 常见问题

**Q：PDF 没有被解析？**  
A：`pip install docling` 或 `pip install pypdf`；中文扫描件可试 MinerU。

**Q：`validate` 报 source_refs 缺失？**  
A：要求模型引用 `context.md` 的条目 ID（如 `DOC-0003`），不要只写“需求文档”。

**Q：生成的用例太多？**  
A：在 `generation.max_cases_per_ac` 限制；先覆盖 P0/P1，再补 P2/P3。

**Q：E2E 不稳定？**  
A：用 API setup、唯一数据、web-first assertion；禁止 sleep；连续跑 3 次。

**Q：没有模型 API key？**  
A：TestForge 本身不调用模型；用宿主 Agent（Claude Code/Codex）或本地模型（Ollama/vLLM）。
