# 5 分钟快速开始

## 前提

- Python 3.8+
- 可选：Node 18+（Playwright）、Docling（PDF 解析）、openpyxl（Excel 导出）
- 可选：Maven/JDK、CMake/编译器、Docker（对应 pack 的验收）

## 0. 选择场景包

```bash
python testforge/testforge.py init --list-packs
```

| Pack | 适用 |
|---|---|
| `python-service` | Python API/服务 |
| `java-service` | Java/Spring 服务 |
| `cpp-cli` | C++ 客户端/CLI |
| `frontend-web` | Web 前端（批次 1 骨架） |
| `k8s` | Kubernetes/集群（批次 1 骨架） |

先 dry-run 看组合：

```bash
python testforge/testforge.py init --stack python-service --target . --dry-run
python testforge/testforge.py init --profile platform --target . --dry-run
python testforge/testforge.py init --detect --target . --dry-run
```

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

# 单场景
python /path/to/TestForge/testforge.py init --target ./your-project --stack python-service
python /path/to/TestForge/testforge.py init --target ./your-project --stack java-service
python /path/to/TestForge/testforge.py init --target ./your-project --stack cpp-cli
```

`--with-ci` 会按 stack 安装 CI 模板：GitHub 写到 `.github/workflows/testforge-<stack>.yml`，GitLab 写到 `.gitlab-ci.<stack>.yml`（需要在 `.gitlab-ci.yml` 里 include）。每个 job 只用 `--stack <id>` 运行本 stack 的 suite 和门禁，不会执行其他 stack 的工具链。模板包含 `run`（生成 run-results）和阻断式 `gate`；覆盖率/变异报告按项目实际配置启用，模板默认用 `--allow-missing-reports`，配置好 mutmut、JaCoCo、PIT、Mull 后应去掉该参数。

## 2. 体检

```bash
cd D:\path\to\your-project
python testforge/testforge.py doctor
```

## 3. 配置

编辑 `testforge.config.json`：

```json
{
  "project": { "name": "my-project", "type": "service", "root": "." },
  "stacks": [
    {
      "id": "api",
      "pack": "python-service",
      "root": ".",
      "commands": { "unit": "uv run pytest -q" }
    }
  ]
}
```

多 stack 时每个 stack 有自己的 `root`、`pack`、`commands`；`init` 会生成 `.testforge/run-manifest.json`，每个 stack 一个 suite。

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
python testforge/testforge.py run --manifest .testforge/run-manifest.json --with-reports
python testforge/testforge.py gate --results .testforge/runs/run-results.json
python testforge/testforge.py report --results .testforge/runs/run-results.json
```

- `run` 默认只跑 `kind=test` 套件；`--with-reports` 才会跑 coverage/mutation 报告套件。
- `gate` 对显式 stack 按 pack 默认解析覆盖率/变异报告，**报告缺失默认失败**；确需容忍时加 `--allow-missing-reports`。
- 旧配置（无 `stacks`）且未声明覆盖率/变异报告时，`gate` 跳过这两项，不会误报失败。
- `gate-report.json` 的 `stacks` 是每个 stack 的门禁结果（`line_coverage`、`mutation_score`、`not_applicable`、`passed`）；`report.md` 会输出 `## Stack: <id>` 分节。

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
