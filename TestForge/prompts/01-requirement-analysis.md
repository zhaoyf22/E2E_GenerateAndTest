# 01 · 需求分析 → 可测项

## 输入

```text
【上下文】
{{.testforge/context/context.md 或指定文件}}

【项目配置】
{{testforge.config.json 的 project / stack / generation 部分}}

【本次范围】
{{要覆盖的模块/AC；不覆盖的内容}}

【输出路径】
.testforge/cases/testable-items.json
```

## 任务

按以下阶段执行，不要跳步。

### 阶段 1：需求清单

- 列出所有验收标准（AC），编号 `AC-001`、`AC-002`……
- 每条保留原文引用与 `source_refs`。
- 标注优先级 P0/P1/P2/P3（按业务影响、使用频率、失败后果）。

### 阶段 2：要素抽取

从文档/设计/接口中抽取：

- 业务规则与约束；
- 输入字段、类型、长度、格式、枚举、默认值、必填/可选；
- 角色与权限矩阵；
- 状态与状态迁移（合法/非法/终态）；
- 异常、补偿、重试、超时、幂等；
- 数据一致性/事务边界；
- 非功能约束（性能、安全、审计、可观测性）。

### 阶段 3：可测项拆分

- 把每个 AC 拆成可独立验证的 `TI-xxx`。
- 每个 TI 关联 AC 与来源。
- 为每个 TI 选择测试设计技术：
  - 输入域 → EP / BVA；
  - 多条件组合 → DT / pairwise；
  - 状态机 → ST；
  - 用户旅程 → scenario；
  - 权限 → permission；
  - 重复请求/消息 → idempotency；
  - 并发写/库存/余额 → concurrency；
  - 接口契约 → contract；
  - 不变量/属性 → property；
  - 经验型缺陷 → error-guessing。

### 阶段 4：信息缺口

- 标记歧义、矛盾、不可测、缺失的信息。
- 每条 gap 写：`gap_id`、描述、影响、需要谁确认。
- 不要把“猜测”写成需求。

### 阶段 5：输出

严格按 `testforge/schemas/testable-items.schema.json` 输出一个 JSON 对象，保存到 `.testforge/cases/testable-items.json`。

## 质量要求

- 每个 AC 至少 1 个 TI；复杂 AC 可拆多个。
- 每个 TI 至少 1 个 technique。
- 高风险路径（跨服务、异步、并发、权限、金额/库存）必须单列。
- 如果文档缺少字段约束，不要编造；写入 gap_list。

## 自检

- 是否有 AC 没有被任何 TI 覆盖？
- 是否有 TI 没有来源？
- 是否有 TI 同时包含多个可独立验证的目标？
- 是否有“待确认”被误写成确定行为？
