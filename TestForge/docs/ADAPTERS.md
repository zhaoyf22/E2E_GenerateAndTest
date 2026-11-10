# 适配器索引

| 适配器 | 文件 | 用途 |
|---|---|---|
| Docling | `adapters/docling.md` | PDF/Word/表格 → 结构化上下文 |
| Schemathesis | `adapters/schemathesis.md` | OpenAPI/GraphQL 属性/契约测试 |
| Playwright | `adapters/playwright.md` | E2E/UI 自动化 |
| pytest | `adapters/pytest.md` | 单元/集成/API 执行基座 |
| Mutation | `adapters/mutation.md` | 覆盖率之外的质量门禁 |
| MCP | `adapters/mcp.md` | 浏览器/Jira/TCMS 工具接入 |

## 推荐组合

| 目标 | 组合 |
|---|---|
| 文档→用例 | Docling + Casely/TestTeller + `test-case-designer` |
| 代码→单测 | pytest/Jest/JUnit + Cover-Agent/AutoCover-Lite + Mutahunter |
| API→契约 | Schemathesis + Pact + `api-test-designer` |
| UI→E2E | Playwright + e2e/Midscene + `e2e-designer` |
| 管理/追溯 | Kiwi TCMS + requirements / TestRail MCP |
| AI 产品 | Promptfoo + DeepEval + Ragas + Inspect AI |

## 新增适配器

1. 在 `adapters/` 新建 `<tool>.md`，写用途/安装/配置/在 TestForge 中的位置/注意事项。
2. 如果影响 CLI，在 `testforge.py` 加解析器或命令。
3. 在 `README.md` 和本文件加链接。
