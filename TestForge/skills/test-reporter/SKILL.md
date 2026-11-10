---
name: test-reporter
description: 汇总运行结果、用例质量、覆盖率、变异分、flaky 和门禁，生成面向研发/QA/产品的发布报告；当用户要求"测试报告/发布门禁/质量总结"时使用。
---

# Test Reporter

## 何时使用

- 测试运行结束，需要给团队/发布评审出报告。
- 需要判断 `GO / CONDITIONAL / BLOCK`。
- 需要把失败分类为产品 bug / 用例问题 / 环境问题 / flaky。

## 输入

- `.testforge/runs/run-results.json`
- `.testforge/reports/validation-report.json`
- `.testforge/reports/gate-report.json`
- `.testforge/cases/coverage-matrix.json`

## 工作流

1. 读取 `prompts/08-report.md`。
2. 汇总：
   - 运行概览：套件通过/失败/超时/错误/耗时；
   - 用例质量：总数、错误/警告、重复、AC 覆盖、可自动化比例；
   - 门禁：指标/阈值/结果；
   - 未覆盖 AC/风险/平台；
   - 失败详情与分类；
   - 缺陷候选；
   - flaky 分析；
   - 下一步 3-5 项。
3. 给发布建议：
   - `BLOCK`：P0 失败、AC 覆盖不足、门禁失败、未分类产品 bug；
   - `CONDITIONAL`：仅 P2/P3 失败、flaky 在阈值内、有规避方案；
   - `GO`：全部门禁通过。
4. 写 `.testforge/reports/report.md`。

## 硬性约束

- 数字必须来自 JSON，不手写。
- 失败项必须带下一步。
- 不确定结论标“待确认”。
- 日志中的密钥/token/PII 必须打码。

## 输出

- `.testforge/reports/report.md`
- 可选：发布评审摘要（一页）

## 参考

- `prompts/08-report.md`
- `prompts/07-repair.md`
