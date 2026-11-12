# Java Service Pack Rules

- Use JUnit 5 + AssertJ; parameterized tests for boundaries and equivalence classes.
- Use Testcontainers for real PostgreSQL/Kafka/Redis; do not use H2 as a substitute for production SQL behavior.
- Stub third-party HTTP with WireMock (`WireMockExtension`, `@DynamicPropertySource`).
- Use Pact for consumer-driven contracts when another service is the consumer.
- Use REST Assured for API E2E and JSON Schema validation.
- Use PIT for mutation testing; surviving mutants indicate assertion gaps.
- jqwik 1.10+ ships with an Anti-AI Usage Clause; confirm before using it for AI-generated tests.
- Use Jazzer for coverage-guided fuzzing of parsers and untrusted input.
- Keep test data isolated; clean up containers and database rows.
