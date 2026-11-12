# 质量门禁

## 指标

| 指标 | 计算 | 建议阈值 | 说明 |
|---|---|---|---|
| AC 覆盖率 | 有 ≥1 条用例的 AC / 总 AC | ≥ 90% | 核心指标 |
| 技术覆盖率 | 使用的技术 / 适用技术 | ≥ 80% | EP/BVA/DT/ST/权限/异常 |
| 可执行率 | 可运行且通过的用例 / 总用例 | ≥ 95% | 生成后必须跑 |
| 重复率 | 相似度 ≥ 阈值的用例对 / 总用例 | ≤ 5% | 语义去重 |
| 行覆盖率 | 执行行 / 总行 | 按基线 | 不要只看数字 |
| 变异分 | 被杀变异体 / 非等价变异体 | ≥ 60% 起 | 抗假测试 |
| flaky 率 | 复跑结果不一致的套件 / 总套件（suite 级代理指标） | ≤ 2% | 连续 3 次；per-test flaky 需测试框架报告 |
| 人工采纳率 | 人工接受用例 / 生成用例 | ≥ 80% | 最贴近业务 |
| 单用例成本 | token/时间/费用 / 用例 | 按预算 | 控制多 Agent 成本 |

> **自动化程度**：`testforge.py gate` 会自动检查 `ac_coverage`、`duplicate_similarity`、`line_coverage`、`line_coverage_delta`、`mutation_score`、`flaky_rate`、`cases_count`。  
> **需人工/外部统计**：技术覆盖率、可执行率、人工采纳率、单用例成本；这些指标用于复盘，不由脚本自动判定。

## 多 stack 门禁

- 每个 stack 的 `coverage.report` / `mutation.report` 相对 **stack root** 解析。
- `coverage.parser` 支持 `coverage.py|jacoco|lcov|cobertura|istanbul|gcovr|none`。
- `mutation.parser` 支持 `json|pit-xml|stryker-json|mutmut|none`。
- `parser: "none"` → `not_applicable`，不失败。
- parser 存在但报告缺失 → 默认 **fail**；加 `--allow-missing-reports` 降级为 warning。
- `gate-report.json` 的 `stacks` 字段是每个 stack 的门禁结果（`line_coverage`、`mutation_score`、`not_applicable`、`passed`）；每个 stack 的 suite 汇总在 `suite_summary`。

## flaky 检测

在 `run-manifest.json` 给套件加 `reruns`：

```json
{
  "suites": [
    {"name": "e2e", "command": "npx playwright test", "reruns": 3, "timeout": 1800}
  ]
}
```

`run` 会执行 3 次；若出现“有时通过、有时失败”，状态记为 `flaky`，并写入 `summary.flaky_rate`。`gate` 用 `flaky_rate_max` 判定。

## 门禁配置

```json
{
  "quality_gates": {
    "ac_coverage_min": 0.9,
    "duplicate_similarity_max": 0.85,
    "line_coverage_min": 0.6,
    "line_coverage_delta_min": 0.0,
    "mutation_score_min": 0.6,
    "flaky_rate_max": 0.02,
    "cases_min": 1
  }
}
```

## 如何设基线

1. 第一次：只记录，不阻断。
2. 第二次：用第一次的值作为 `baseline`，设 `delta_min=0`（不下降）。
3. 稳定后：逐步提高 `line_coverage_min` / `mutation_score_min`。
4. 关键模块：单独设更高阈值；非关键模块可放宽。

## 常见误用

- 只看覆盖率：`assert True` 也能刷高；必须配变异分/断言审查。
- 只看用例条数：大量重复/空泛用例没有价值。
- 变异分一刀切：等价变异体会拉低分数；要分类。
- 忽略 flaky：不稳定的测试会让团队失去信任。
- 门禁太严：第一次就要求 90% 变异分会阻塞交付；先基线。

## 输出

`gate-report.json`：

```json
{
  "passed": false,
  "checks": [
    {"name": "ac_coverage", "value": 0.82, "threshold": 0.9, "passed": false}
  ],
  "failures": [...]
}
```

CI 中把 `gate` 的非 0 退出码作为阻断条件。
