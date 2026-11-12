# Java Service Example

Minimal Maven + JUnit 5 service example.

```bash
cd examples/java-service
mvn -q test
cd ../..
python testforge.py validate --cases examples/java-service/test-cases.sample.json --requirements examples/java-service/requirements.json
```

Requires JDK 17+ and Maven. For Testcontainers/WireMock/Pact examples, add the corresponding dependencies and use the pack templates.
