# pytest 适配

## 用途

单元/集成/API 测试的执行基座。TestForge 生成 pytest 测试并运行。

## 安装

```bash
pip install pytest pytest-cov
# 可选
pip install pytest-xdist pytest-rerunfailures pytest-testmon
```

## 目录建议

```text
tests/
├── unit/
├── integration/
├── api/
├── conftest.py
└── fixtures/
```

## 约定

- 外部依赖用 fixture + mock/fake；集成测试用 Testcontainers 或 docker-compose。
- 测试数据固定种子，唯一值，清理。
- 断言行为/契约，不测私有方法。
- 覆盖率：
  ```bash
  pytest --cov=src --cov-report=json:coverage.json --cov-report=term-missing
  ```
- 并行：
  ```bash
  pytest -n auto
  ```
- flaky 复跑：
  ```bash
  pytest --reruns 2 --reruns-delay 1
  ```
- 影响分析：
  ```bash
  pytest --testmon
  ```

## 在 TestForge 中

```bash
python testforge/testforge.py run --manifest .testforge/run-manifest.json
python testforge/testforge.py gate --results .testforge/runs/run-results.json --coverage coverage.json
```

## 注意

- `pytest-testmon` 需要先全量跑一次建立 `.testmondata`。
- 生成测试必须能独立跑；不要依赖其他测试创建的全局状态。
- 变异测试用 `mutmut`，与覆盖率一起看。
