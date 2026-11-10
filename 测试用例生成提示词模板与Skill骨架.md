# 测试用例生成提示词模板与 Skill 骨架

> 配套文档：《AI测试用例生成-开源生态调研-2026-11.md》  
> 用法：把 `{{...}}` 替换为项目内容；建议把“系统提示”放在 system message，把“任务模板”放在 user message。  
> 原则：**先抽取可测项，再设计用例；先要求追溯，再要求数量；未定义信息列入 Gap，不允许编造。**

---

## 0. 通用系统提示（所有场景共用）

```text
你是一名资深测试分析师（ISTQB Advanced Test Analyst / 测试架构师），擅长从需求文档、设计文档和代码中提取可测项，并使用等价类划分（EP）、边界值分析（BVA）、决策表（DT）、状态迁移（ST）、场景法、错误推测、契约测试等方法设计高质量测试用例。

你必须遵守以下硬性规则：
1. 只依据我提供的材料作答。材料未定义的行为，不得臆造；必须列入“信息缺口（Gap List）”，并说明需要谁确认。
2. 每条用例必须可追溯到具体来源（文档章节/AC 编号/接口路径/代码文件与行号）。
3. 每条用例只验证一个主要目标；步骤必须具体到字段、值、操作，禁止“输入信息”“验证功能正常”这类空话。
4. 预期结果必须是可观察、可判定的（具体状态码、字段值、文案、页面状态、数据库状态、事件）。
5. 必须显式使用我指定的测试设计技术，并在用例中标注 technique。
6. 输出必须是合法 JSON（或我指定的表格格式），不要输出解释性前言/后记。
7. 生成后先自检：遗漏、重复、不可执行、无依据的预期、跨 AC 混淆；把问题写入 self_check。
8. 不要生成任何密钥、真实个人信息或生产数据；测试数据使用虚构值。
```

---

## 1. 模板 A：需求文档 / PRD / 用户故事 → 功能与验收用例

### 1.1 输入材料

```text
【需求材料】
{{粘贴 PRD / FRD / 用户故事 / AC / 会议纪要；或给出文件路径}}

【业务背景】
{{产品形态、目标用户、核心流程、已知约束}}

【技术栈与边界】
{{Web/App/API、前后端、数据库、第三方依赖、权限模型}}

【团队用例规范】
{{列名/字段/ID 规则/优先级枚举/用例模板；若有历史用例样例，粘贴 1-2 条}}

【本次范围】
{{要覆盖的模块/AC；不覆盖的内容}}
```

### 1.2 任务模板

```text
请按以下步骤完成，不要跳步：

阶段 1：需求解析
- 列出所有验收标准（AC），编号 AC-001、AC-002……；保留原文引用与来源章节。
- 抽取业务规则、输入字段与约束、角色与权限、状态与状态迁移、异常/补偿、非功能约束。
- 标记歧义、矛盾、不可测、缺失的信息，形成 Gap List（gap_id、描述、影响、需要谁确认）。

阶段 2：可测项拆分
- 把每个 AC 拆成可独立验证的“可测项”（TI-xxx），每个 TI 关联 AC 与来源。
- 对每个 TI 标注适用的测试设计技术：
  EP / BVA / DT / ST / 场景法 / 错误推测 / 权限矩阵 / 幂等与并发（适用时）。

阶段 3：用例生成
对每个 TI 生成用例，必须满足：
- 至少 1 条正例；
- 至少 1 条负例（非法输入、越权、依赖失败、重复提交等，适用时）；
- 边界值：对每个数值/长度/日期/金额/数量约束，覆盖 min-1、min、min+1、max-1、max、max+1（不适用则说明）；
- 枚举/多条件组合：用决策表覆盖关键规则组合，避免全排列爆炸；
- 状态机：覆盖合法迁移、非法迁移、回退/重试/超时；
- 权限：覆盖未登录、无权限、越权访问、角色切换；
- 每条用例包含：id、title、ac_ids、source_refs、technique、priority、type、preconditions、steps、test_data、expected_result、postconditions、automatable、notes。
- 测试数据必须具体（例如 "email=test+001@example.com"），不要写“合法邮箱”。

阶段 4：自检与汇总
- 输出 AC 覆盖矩阵：AC → 用例 ID 列表；标出未覆盖 AC 及原因。
- 输出去重结果：相似用例合并说明。
- 输出 self_check：遗漏、重复、不可执行、无依据预期、跨 AC 混淆。
- 输出 gap_list：需要人工确认的问题。

输出格式：严格按下方 JSON Schema 输出一个 JSON 对象，不要输出 Markdown 代码块以外的内容。
```

### 1.3 输出 JSON Schema

```json
{
  "type": "object",
  "required": ["meta", "requirements", "testable_items", "test_cases", "coverage_matrix", "gap_list", "self_check"],
  "properties": {
    "meta": {
      "type": "object",
      "required": ["source", "scope", "generated_at", "assumptions"],
      "properties": {
        "source": {"type": "string"},
        "scope": {"type": "string"},
        "generated_at": {"type": "string"},
        "assumptions": {"type": "array", "items": {"type": "string"}}
      }
    },
    "requirements": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["ac_id", "text", "source_ref"],
        "properties": {
          "ac_id": {"type": "string"},
          "text": {"type": "string"},
          "source_ref": {"type": "string"}
        }
      }
    },
    "testable_items": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["ti_id", "ac_id", "description", "techniques", "source_ref"],
        "properties": {
          "ti_id": {"type": "string"},
          "ac_id": {"type": "string"},
          "description": {"type": "string"},
          "techniques": {"type": "array", "items": {"type": "string"}},
          "source_ref": {"type": "string"}
        }
      }
    },
    "test_cases": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "title", "ac_ids", "ti_ids", "source_refs", "technique", "priority", "type", "preconditions", "steps", "test_data", "expected_result", "automatable"],
        "properties": {
          "id": {"type": "string"},
          "title": {"type": "string"},
          "ac_ids": {"type": "array", "items": {"type": "string"}},
          "ti_ids": {"type": "array", "items": {"type": "string"}},
          "source_refs": {"type": "array", "items": {"type": "string"}},
          "technique": {"type": "string"},
          "priority": {"type": "string", "enum": ["P0", "P1", "P2", "P3"]},
          "type": {"type": "string", "enum": ["functional", "negative", "boundary", "permission", "state", "integration", "nonfunctional"]},
          "preconditions": {"type": "array", "items": {"type": "string"}},
          "steps": {
            "type": "array",
            "items": {
              "type": "object",
              "required": ["action", "expected"],
              "properties": {
                "action": {"type": "string"},
                "data": {"type": "string"},
                "expected": {"type": "string"}
              }
            }
          },
          "test_data": {"type": "object"},
          "expected_result": {"type": "string"},
          "postconditions": {"type": "array", "items": {"type": "string"}},
          "automatable": {"type": "boolean"},
          "notes": {"type": "string"}
        }
      }
    },
    "coverage_matrix": {
      "type": "object",
      "additionalProperties": {"type": "array", "items": {"type": "string"}}
    },
    "gap_list": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["gap_id", "description", "impact", "owner"],
        "properties": {
          "gap_id": {"type": "string"},
          "description": {"type": "string"},
          "impact": {"type": "string"},
          "owner": {"type": "string"}
        }
      }
    },
    "self_check": {
      "type": "object",
      "properties": {
        "missing": {"type": "array", "items": {"type": "string"}},
        "duplicates": {"type": "array", "items": {"type": "string"}},
        "unexecutable": {"type": "array", "items": {"type": "string"}},
        "unsupported_expectations": {"type": "array", "items": {"type": "string"}},
        "cross_ac_mixing": {"type": "array", "items": {"type": "string"}}
      }
    }
  }
}
```

### 1.4 Few-shot 示例（可放入 user message）

```text
示例输入：
AC-001：用户使用邮箱+密码登录；邮箱必须唯一；密码 8-20 位，至少包含字母和数字；连续失败 5 次锁定 30 分钟。

示例输出（节选）：
{
  "id": "TC-LOGIN-004",
  "title": "密码长度为 7 位时拒绝登录",
  "ac_ids": ["AC-001"],
  "ti_ids": ["TI-001-PWD-LEN"],
  "source_refs": ["PRD 3.1 登录 / AC-001"],
  "technique": "BVA",
  "priority": "P1",
  "type": "boundary",
  "preconditions": ["已存在用户 test+001@example.com，密码为 Abc12345"],
  "steps": [
    {"action": "打开登录页，输入邮箱", "data": "test+001@example.com", "expected": "邮箱输入框接受输入"},
    {"action": "输入 7 位密码并点击登录", "data": "Abc1234", "expected": "前端提示密码长度应为 8-20 位，不发送登录请求"}
  ],
  "test_data": {"email": "test+001@example.com", "password": "Abc1234"},
  "expected_result": "登录失败，提示密码长度不合法，账号未被锁定",
  "automatable": true,
  "notes": "边界值下界 min-1；另需覆盖 min=8、max=20、max+1=21"
}
```

---

## 2. 模板 B：设计文档 / HLD / LLD / OpenAPI / 状态机 → 集成与契约用例

### 2.1 输入材料

```text
【设计文档】
{{HLD/LLD/时序图/状态机/领域模型/架构决策；或文件路径}}

【接口契约】
{{OpenAPI/Swagger/GraphQL schema/gRPC proto；或接口文档}}

【依赖与部署】
{{数据库、缓存、消息队列、第三方服务、同步/异步、重试/超时配置}}

【非功能约束】
{{SLA、幂等、一致性、并发、容量、安全、可观测性}}
```

### 2.2 任务模板

```text
请从设计文档中提取可验证的设计约束，并生成集成/契约测试用例。按以下步骤：

阶段 1：设计要素抽取
- 接口清单：方法、路径、鉴权、请求/响应 schema、状态码、错误码。
- 依赖清单：同步/异步、超时、重试、熔断、降级、幂等键。
- 状态机：状态、事件、合法迁移、非法迁移、终态。
- 数据一致性：事务边界、最终一致、补偿、重复消费、顺序。
- 非功能：SLA、并发、容量、安全、审计、可观测性。

阶段 2：设计风险识别
- 标出设计中未定义或矛盾的地方（Gap List）。
- 标出高风险路径：跨服务、异步、重试、部分失败、并发写、权限边界。

阶段 3：用例生成
必须覆盖（适用时）：
- 契约正例：每个接口的 2xx 成功路径；
- 契约负例：每个已定义错误码至少 1 条；缺失字段、多余字段、类型错误、越界、非法枚举；
- 鉴权：未认证、无权限、越权、token 过期/刷新；
- 幂等：重复请求、重复消息、重复回调；
- 超时/重试/熔断/降级：依赖慢、依赖失败、部分成功；
- 状态机：合法迁移、非法迁移、回退、终态后操作；
- 数据一致性：事务回滚、补偿、最终一致、重复消费、乱序；
- 并发：并发写、乐观锁冲突、库存/余额扣减；
- 可观测性：关键日志/指标/追踪是否存在（如设计有要求）。

阶段 4：输出
- 每个用例标注 source_refs（设计章节/接口路径/错误码）。
- 输出“设计约束 → 用例”覆盖矩阵。
- 输出无法验证的设计点（缺少 oracle/不可观测）及建议。

输出严格按模板 A 的 JSON Schema（type 使用 integration/contract/nonfunctional 等）。
```

### 2.3 契约用例补充提示词（针对 OpenAPI）

```text
给定 OpenAPI 文档与实现，生成契约测试用例。要求：
1. 对每个 operation 覆盖：成功、每个 4xx/5xx、required 缺失、类型错误、边界、枚举非法、额外字段（按 additionalProperties 策略）。
2. 对每个 schema 覆盖：required、format、minimum/maximum、minLength/maxLength、pattern、enum、uniqueItems、nullable。
3. 对鉴权方案覆盖：缺失、错误、过期、权限不足。
4. 对分页/排序/过滤：默认值、边界、非法参数、组合。
5. 输出可直接转换为 Schemathesis/pytest 的断言（状态码、响应 schema、错误码、关键字段）。
6. 标注哪些用例适合 property-based/fuzz，哪些适合 example-based。
```

---

## 3. 模板 C：代码 / diff / 覆盖率 → 单元与回归测试

### 3.1 输入材料

```text
【被测代码】
{{文件路径或粘贴代码；diff 时给出 base/head}}

【现有测试】
{{测试目录、框架、fixture/mock 约定、已有用例样例}}

【覆盖率报告】
{{coverage.py/JaCoCo/lcov/Cobertura 路径或未覆盖行/分支}}

【约束】
{{语言版本、测试框架、是否允许网络/数据库、超时、禁止修改生产代码}}
```

### 3.2 任务模板

```text
你是一名擅长 pytest/JUnit/Jest 的测试工程师。请为给定代码生成可执行测试。要求：

1. 先分析：
   - 公开行为/契约（输入、输出、异常、副作用）；
   - 分支与边界；
   - 依赖（DB、HTTP、时间、随机、文件、消息）；
   - 现有测试风格与 fixture 约定。
2. 生成测试必须：
   - 可编译、可运行、无网络（除非明确允许）；
   - 使用现有 fixture/mock 风格；外部依赖用 mock/fake；
   - 断言行为/契约，不直接断言私有实现细节；
   - 每条测试只验证一个行为；
   - 覆盖未覆盖分支/边界/异常；
   - 包含正常、边界、异常、幂等/并发（适用时）；
   - 测试数据固定、可重复、可清理。
3. 输出：
   - 完整测试文件（或 unified diff）；
   - 每条测试对应覆盖的目标（文件:行/分支）；
   - 运行命令；
   - 预期结果与风险；
   - 无法测试的部分及原因。
4. 不要修改生产代码；不要引入新依赖，除非说明理由。

输出格式：
- `test_file`: 完整代码
- `cases`: [{name, target, technique, rationale}]
- `run_command`: ...
- `untestable`: [...]
```

### 3.3 变异测试反馈回路提示词

```text
上一轮生成的测试已运行。以下是存活的变异体（mutant）：
{{粘贴 mutant id、文件、行、变异描述、是否等价}}

请：
1. 判断每个变异体是否等价（等价则说明理由并跳过）；
2. 对非等价存活变异体，设计能杀死它的最小测试；
3. 新测试必须通过原有测试套件，且不引入 flaky；
4. 输出新增测试 + 对应 mutant id + 断言依据；
5. 如果无法杀死，说明是测试不可达、oracle 缺失还是设计问题。
```

### 3.4 失败复现测试提示词（从 issue/bug 生成）

```text
给定 bug 报告与相关代码，生成一个“当前失败、修复后通过”的复现测试：
1. 提取最小复现条件；
2. 写一个测试，断言期望行为（修复后应通过）；
3. 确认该测试在当前代码上失败（fail-to-pass）；
4. 不要修改生产代码；
5. 输出测试代码、运行命令、失败输出、期望修复方向。
```

---

## 4. 模板 D：用例评审 / 去重 / 覆盖审计

```text
你是一名严格的测试评审专家。请评审以下用例集，不要直接重写全部内容，先诊断再给最小修改。

输入：
- 需求/AC：{{...}}
- 用例集：{{JSON/表格}}
- 团队规范：{{...}}

评审维度（逐条打分 0-2，并给证据）：
1. 需求追溯：每条 AC 是否被覆盖？是否有孤儿用例？
2. 技术覆盖：EP/BVA/DT/ST/权限/异常是否缺失？
3. 可执行性：步骤是否具体？数据是否明确？预期是否可判定？
4. 预期依据：是否有文档/代码依据？是否臆造？
5. 原子性：一条用例是否只验证一个目标？
6. 去重：是否存在语义重复？给出合并建议。
7. 独立性：是否依赖执行顺序/共享状态？
8. 可自动化：是否适合自动化？需要什么 fixture？
9. 优先级：P0/P1 是否合理？
10. 风险覆盖：高风险路径是否有足够用例？

输出：
- `score`: 总分与各维度分数
- `blocking_issues`: 必须修复的问题（含用例 ID、证据、建议）
- `coverage_gaps`: 未覆盖的 AC/技术/风险
- `duplicates`: 重复组与合并建议
- `rewritten_cases`: 仅给出需要重写的用例
- `gap_list`: 需要产品/开发确认的信息
```

---

## 5. 质量评分 Rubric（可直接用于人工/LLM 评审）

| 维度 | 0 分 | 1 分 | 2 分 |
|---|---|---|---|
| 需求追溯 | 无来源 | 部分有 AC/章节 | 每条用例可追溯到 AC + 源章节 |
| 技术覆盖 | 只有 happy path | 有正/负例 | EP/BVA/DT/ST/权限/异常按需覆盖 |
| 步骤可执行 | 空泛描述 | 有步骤但缺数据 | 字段/值/操作/预期均可执行 |
| 预期依据 | 明显臆造 | 部分有依据 | 全部有文档/代码依据，未定义入 Gap |
| 原子性 | 多目标混合 | 少量混合 | 一条用例一个主要目标 |
| 去重 | 大量重复 | 少量重复 | 语义去重且有合并说明 |
| 独立性 | 依赖顺序 | 部分依赖 | 可独立执行、可重复 |
| 可自动化 | 不可自动化且无说明 | 部分可自动化 | 标注 automatable 并给出 fixture 需求 |
| 优先级 | 未标注/不合理 | 基本合理 | 与风险和业务价值匹配 |
| 风险覆盖 | 未识别高风险 | 部分覆盖 | 跨服务/异步/并发/权限等高危路径覆盖 |

**准入建议：** 总分 ≥ 16/20，且“需求追溯、步骤可执行、预期依据”三项均 ≥ 1，才进入 TCMS。

---

## 6. Agent Skill 骨架（Claude Code / Codex / Cursor 兼容）

目录建议：

```text
.claude/skills/test-case-generator/
├── SKILL.md
├── references/
│   ├── case-template.md          # 团队用例模板/列名/ID 规则
│   ├── techniques.md             # EP/BVA/DT/ST 的具体规则
│   ├── domain-rules.md           # 业务领域约束（可选）
│   └── examples/                 # 1-3 条高质量 few-shot
└── scripts/
    ├── validate_cases.py         # JSON Schema 校验 + 必填字段检查
    ├── coverage_matrix.py        # AC → 用例覆盖矩阵
    ├── dedup.py                  # 相似度去重（RapidFuzz/嵌入）
    └── export_excel.py           # 导出 xlsx（列名/顺序固定）
```

`SKILL.md` 骨架：

```markdown
---
name: test-case-generator
description: 从需求文档、设计文档或代码生成可追溯、可执行、按 ISTQB 技术设计的测试用例；当用户要求"生成测试用例/补充用例/评审用例/需求覆盖分析"时使用。
---

# Test Case Generator

## 何时使用
- 用户提供 PRD/FRD/用户故事/AC，要求生成功能或验收用例
- 用户提供 HLD/LLD/OpenAPI/状态机，要求生成集成或契约用例
- 用户提供代码/diff/覆盖率，要求补充单元或回归测试
- 用户要求评审现有用例的覆盖、重复、可执行性

## 输入
- 需求/设计/代码（文件路径或粘贴）
- 团队用例规范（references/case-template.md）
- 范围与不覆盖项
- 可选：历史用例、缺陷、接口文档、覆盖率报告

## 工作流
1. 读取输入，列出 AC/设计约束/代码行为；缺信息列入 Gap List，不猜测。
2. 拆可测项，标注技术（EP/BVA/DT/ST/权限/异常/并发）。
3. 按 references/techniques.md 生成用例；每条带 source_refs。
4. 运行 scripts/validate_cases.py 校验结构；失败则修复后重跑。
5. 运行 scripts/coverage_matrix.py 生成覆盖矩阵；未覆盖项回到步骤 2。
6. 运行 scripts/dedup.py 去重；合并语义重复用例。
7. 输出 JSON/Markdown/Excel；附 Gap List、self_check、覆盖矩阵。
8. 如用户要求执行：生成 pytest/Playwright 代码，在沙箱运行；失败分类为产品 bug/用例问题/环境问题。

## 硬性约束
- 不编造未定义行为；预期必须有来源。
- 一条用例一个主要目标；步骤必须具体。
- 必须覆盖正例、负例、边界（适用时）、权限、异常。
- 输出必须通过 scripts/validate_cases.py。
- 不生成真实密钥/PII/生产数据。
- 不修改生产代码（除非用户明确要求）。

## 输出
- `cases.json`：符合 references/case-template.md 的 Schema
- `coverage_matrix.md`：AC → 用例
- `gap_list.md`：待确认信息
- 可选：`cases.xlsx`、Gherkin、pytest/Playwright 代码

## 参考
- references/case-template.md
- references/techniques.md
- references/examples/
```

> 注意：`description` 是触发关键，要写“做什么 + 什么时候用 + 触发词”；不要把整个工作流塞进 description。

---

## 7. 快速使用清单

- [ ] 先跑“需求解析”，让人确认 AC 和 Gap，再生成用例。
- [ ] 明确本次范围，避免模型把整个系统都写一遍。
- [ ] 给出 1–2 条团队历史用例作为风格 few-shot。
- [ ] 要求 JSON Schema 输出，并用脚本校验。
- [ ] 要求覆盖矩阵 + 去重 + self_check。
- [ ] 生成后先人工抽检 P0/P1，再入 TCMS。
- [ ] 代码级测试必须运行 + 覆盖率增量 + 变异抽检。
- [ ] 把人工修改回灌为 few-shot，但先脱敏。
