# Mutahunter

- Repo: https://github.com/codeintegrity-ai/mutahunter
- LLM-generated mutants + LLM test generation; language-agnostic via coverage reports.
- Use it after `coverage.py` and before accepting a test suite.
- Filter equivalent mutants; do not chase mutation score blindly.
- Export a `mutation-report.json` with `mutation_score` for TestForge `gate`.
