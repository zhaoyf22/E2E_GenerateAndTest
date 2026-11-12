# Jazzer

- Coverage-guided fuzzing for JVM (Java/Kotlin), with auto-shrinking and corpus reuse.
- Use it for parsers, protocol handlers, deserialization, and untrusted input.
- Combine with JUnit 5 tests; keep fuzz runs time-boxed in CI.
- Treat crashes and unexpected exceptions as findings; add a deterministic regression test.
