# Python Service Pack Rules

- Use pytest 9.x conventions; prefer fixtures over setup/teardown classes.
- Mock only boundaries (HTTP, clock, filesystem, third-party SDKs). Use Testcontainers for real PostgreSQL/Redis/Kafka.
- Use `freezegun` or an injected clock for time-dependent behavior.
- Prefer branch coverage over line coverage; `pytest --cov=src --cov-branch`.
- For OpenAPI, use Schemathesis property tests in addition to example-based cases.
- For invariants and state machines, use Hypothesis (`@given`, `RuleBasedStateMachine`).
- For mutation feedback, use mutmut; treat surviving mutants as test gaps, not score chasing.
- Do not assert private methods or implementation details; assert public behavior.
- Keep test data unique and clean up; never use real customer data.
