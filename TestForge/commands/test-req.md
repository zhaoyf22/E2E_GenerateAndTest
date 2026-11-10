---
description: 需求分析：从文档/设计/接口抽取 AC、可测项、风险和 Gap
argument-hint: "[模块名或文档路径]"
---

# /test-req

用户参数：`$ARGUMENTS`

执行：

1. 确认 `.testforge/context/context.md` 存在；不存在则运行：
   ```bash
   python testforge/testforge.py pack --with-diff
   ```
2. 调用 `requirement-analyst` subagent，读取：
   - `testforge/prompts/00-system.md`
   - `testforge/prompts/01-requirement-analysis.md`
   - `.testforge/context/context.md`
   - `testforge.config.json`
3. 输出 `.testforge/cases/testable-items.json`，符合 `schemas/testable-items.schema.json`。
4. 校验结构：
   ```bash
   python testforge/testforge.py validate --cases .testforge/cases/testable-items.json --kind testable
   ```
5. 生成 Gap List，按“必须确认/建议确认”分组。
6. 汇报：
   - AC 数、TI 数、Gap 数；
   - 高风险路径；
   - 下一步：确认 Gap 后 `/test-design`。

不要生成详细用例；不要编造未定义行为。
