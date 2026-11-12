# Pynguin

- Repo: https://github.com/se2p/pynguin
- Search-based Python test generator; deterministic and complementary to LLM generation.
- Run on a module or package, then merge generated tests into `tests/generated/`.
- Generated tests can be flaky; seed the RNG and rerun 3 times before accepting.
- Use it when coverage is low and you want a deterministic baseline.
