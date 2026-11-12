# Qodo Cover (formerly Cover-Agent)

- Repo: https://github.com/qodo-ai/qodo-cover
- Supports Python/Java/Go/JS/TS/PHP/Kotlin officially; **C++ is not officially supported**.
- Use it to generate coverage-driven unit tests, then run TestForge `validate`/`gate`.
- It uses LiteLLM, so point it at the same provider as the rest of the project.
- Treat generated assertions as drafts; run mutation testing before accepting them.
