# AI 测试用例生成与自动化：调研 + 可落地套件

本目录包含从“调研”到“可执行套件”的三层产出。

## 1. 调研

- `AI测试用例生成-开源生态调研-2026-11.md`  
  开源 Agent / Skills / 工具 / 提示词 / 框架的全景与选型。
- `调研审查-补遗-与TOP10推荐-2026-11.md`  
  二次审查：补遗（文档解析、TCMS/追溯、契约/属性/变异、测试影响分析、LLM/Agent 评测、Skills 供应链安全）+ 分类对比 + TOP10。
- `测试用例生成提示词模板与Skill骨架.md`  
  需求/设计/代码三套提示词、JSON Schema、评审 Rubric、SKILL.md 骨架。

## 2. 可落地套件

`TestForge/` 是通用套件，可直接 `init` 到已有项目：

```bash
python TestForge/testforge.py init --target D:\path\to\your-project --profile platform --with-ci
cd D:\path\to\your-project
python testforge/testforge.py doctor
python testforge/testforge.py pack
```

支持 profile：`platform`（前端+后端）、`service`（单服务）、`cli`（客户端工具）、`frontend`、`backend`。

包含：

- `testforge.py`：pack / validate / matrix / export / run / gate / report / doctor
- `prompts/`：9 个阶段提示词
- `skills/`：7 个 Agent Skills
- `agents/`：7 个 Subagents
- `commands/`：7 个 Slash commands
- `schemas/`：4 个 JSON Schema
- `templates/`：用例/Gherkin/Playwright/pytest/API/测试计划/缺陷
- `adapters/`：Docling / Schemathesis / Playwright / pytest / mutation / MCP
- `ci/`：GitHub Actions / GitLab CI
- `examples/`：platform / service / cli 三个示例

## 3. 建议阅读顺序

1. `TestForge/QUICKSTART.md`（5 分钟跑通）
2. `TestForge/README.md`（能力与结构）
3. `TestForge/docs/WORKFLOW.md`（完整流程）
4. `TestForge/docs/QUALITY-GATES.md`（门禁指标）
5. `TestForge/docs/SECURITY.md`（数据/Skill 供应链/MCP 安全）
6. `TestForge/docs/REVIEW-2026-11-10.md`（套件审查、已修问题、剩余限制）
