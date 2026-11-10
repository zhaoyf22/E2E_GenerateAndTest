---
name: requirement-analyzer
description: 从 PRD/需求文档/设计文档/接口文档中抽取验收标准、业务规则、状态机、权限、边界和信息缺口；当用户要求"分析需求/拆测试点/做需求追溯/找出歧义"时使用。
---

# Requirement Analyzer

## 何时使用

- 用户提供 PRD/FRD/用户故事/AC/设计文档/接口文档，要求分析可测项。
- 用户要求“需求评审”“找歧义/矛盾/不可测点”“生成追溯矩阵”。
- 在生成测试用例之前，作为第一步。

## 输入

- `testforge.config.json`：项目类型、输入路径、技术栈。
- `.testforge/context/context.md` 或指定文档。
- 本次范围（模块/AC/不覆盖项）。

## 工作流

1. 运行/确认上下文已打包：
   ```bash
   python testforge/testforge.py pack
   ```
2. 读取 `prompts/01-requirement-analysis.md`，按阶段执行。
3. 抽取：
   - AC 清单（AC-001…），每条带 `source_refs`；
   - 字段/约束/枚举/默认值；
   - 角色权限矩阵；
   - 状态机（状态/事件/合法迁移/非法迁移/终态）；
   - 异常/补偿/重试/超时/幂等；
   - 数据一致性/事务；
   - 非功能约束。
4. 拆可测项（TI-xxx），标注技术：
   `EP/BVA/DT/ST/scenario/error-guessing/permission/idempotency/concurrency/contract/property/pairwise`。
5. 输出 `gap_list`：歧义、矛盾、不可测、缺失信息、需要谁确认。
6. 写入 `.testforge/cases/testable-items.json`，符合 `schemas/testable-items.schema.json`。
7. 校验结构：
   ```bash
   python testforge/testforge.py validate --cases .testforge/cases/testable-items.json --kind testable
   ```

## 硬性约束

- 不编造未定义行为；不确定的放 `gap_list`。
- 每个 AC 至少 1 个 TI；每个 TI 至少 1 个技术。
- 高风险路径（跨服务、异步、并发、权限、金额/库存）必须单列。
- 不要在这一步直接写详细用例；只到可测项。

## 输出

- `.testforge/cases/testable-items.json`
- 一份给产品/开发确认的 Gap List（Markdown 或 JSON）。

## 参考

- `prompts/01-requirement-analysis.md`
- `schemas/testable-items.schema.json`
- `templates/test-plan.md`
