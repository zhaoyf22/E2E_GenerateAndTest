---
description: 初始化 TestForge：检查配置、打包上下文、生成第一版可测项
argument-hint: "[profile: platform|service|cli|frontend|backend]"
---

# /test-init

用户参数：`$ARGUMENTS`

执行：

1. 如果当前项目没有 `testforge.config.json`：
   - 根据参数或项目结构选择 profile；
   - 提示用户运行：
     ```bash
     python testforge/testforge.py init --target . --profile <profile>
     ```
2. 运行体检：
   ```bash
   python testforge/testforge.py doctor
   ```
3. 打包上下文：
   ```bash
   python testforge/testforge.py pack --with-diff
   ```
4. 读取 `testforge/prompts/01-requirement-analysis.md`，调用 `requirement-analyst` subagent：
   - 生成 `.testforge/cases/testable-items.json`；
   - 输出 Gap List。
5. 汇报：
   - 配置是否完整；
   - 上下文条目数/不支持的文件；
   - AC/TI/Gap 数量；
   - 下一步：人工确认 Gap，然后 `/test-design`。

不要在这一步生成详细用例。
