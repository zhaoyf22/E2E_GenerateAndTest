# MCP 适配

## 用途

把浏览器、Jira/Confluence、TestRail/Xray/Kiwi、文件系统等工具接给 Agent。TestForge 的 skills/agents 可以通过 MCP 读写外部系统。

## 常用 MCP

| MCP | 用途 | 注意 |
|---|---|---|
| Playwright MCP | 驱动浏览器、复现 bug | 不是测试生成器；token 消耗 |
| Chrome DevTools MCP | console/network/性能/内存诊断 | 仅 Chrome；调试用 |
| Atlassian MCP | 读 Jira/Confluence | 只读优先 |
| TestRail MCP | 用例/运行/结果 CRUD | 写入要显式开关 |
| Xray MCP | Jira Cloud 测试管理 | 商业 Xray |
| Kiwi TCMS MCP | 开源 TCMS | 需自部署 Kiwi |
| Figma MCP | 读设计稿 | 需要访问权限 |

## 安全原则

1. **最小权限**：只给必要的读/写工具；删除/批量写入默认关闭。
2. **只读优先**：需求/设计读取用只读 token；用例入库单独授权。
3. **审计**：记录谁在什么时候写了什么。
4. **脱敏**：不要把密钥/PII 传给 MCP。
5. **隔离**：测试环境专用账号，不使用生产管理员。

## 在 TestForge 中

- `skills/casely-qa-skill` 可用 Atlassian MCP 读 Jira/Confluence。
- `skills/e2e-designer` 可用 Playwright MCP 驱动/复现。
- `scripts`/`testforge.py` 不直接依赖 MCP；MCP 是宿主 Agent 的能力。

## 配置示例（Claude Code）

在 `.claude/settings.json` 或宿主配置中加入 MCP server（具体格式以宿主文档为准）。不要提交 token 到 Git。
