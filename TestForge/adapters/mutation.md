# 变异测试适配

## 用途

判断测试是否真的能发现缺陷。覆盖率可以被 `assert True` 刷高，变异分更抗刷。

## 工具

| 语言 | 工具 |
|---|---|
| Python | `mutmut`、`cosmic-ray` |
| Java | PIT/pitest |
| JS/TS | Stryker |
| C# | Stryker.NET |
| Rust | cargo-mutants |
| PHP | Infection |
| 多语言 + LLM | Mutahunter |

## Python 快速使用

```bash
pip install mutmut
mutmut run
mutmut results
mutmut html
```

## Java

```bash
mvn org.pitest:pitest-maven:mutationCoverage
```

## JS/TS

```bash
npx stryker run
```

## 在 TestForge 中

1. 生成测试并确保通过。
2. 跑变异测试，得到 `mutation_score`。
3. 写入 JSON：
   ```json
   {"mutation_score": 0.72}
   ```
4. 门禁：
   ```bash
   python testforge/testforge.py gate \
     --results .testforge/runs/run-results.json \
     --mutation mutation-report.json
   ```

## 注意

- 先基线，再定阈值；不要一上来要求 90%。
- 存活变异体分类：真实缺口 / 等价变异体 / 不可达。
- LLM 生成的变异体（Mutahunter）需要等价性筛查，否则噪声大。
- 变异测试计算贵；按 diff/关键模块跑，不要全仓每次跑。
