# java-service acceptance

```bash
cd <repo>/TestForge
python testforge.py init --profile java-service --target <tmp> --dry-run
python testforge.py init --profile java-service --target <tmp>
python -m unittest tests.test_pack_java -v
mvn -q -f examples/java-service/pom.xml test
python testforge.py validate --cases examples/java-service/test-cases.sample.json --requirements examples/java-service/requirements.json
python testforge.py scaffold --cases examples/java-service/test-cases.sample.json --stack svc --config <tmp>/testforge.config.json --out <tmp>/scaffold
```

Expected: init dry-run prints a config with one `svc` stack (the `java-service` profile); pack test passes; Maven example passes; validate exits 0; scaffold writes a disabled JUnit 5 test.

Report-artifact check (when Maven/PIT are installed): `mvn -q org.pitest:pitest-maven:mutationCoverage` writes `target/pit-reports/mutations.xml`, and `gate` parses it with the `pit-xml` parser. JaCoCo's `target/site/jacoco/jacoco.xml` is parsed with `jacoco`.

Known limitation: scaffold templates hardcode the `com.example` package because TestForge does not infer Java package names; move generated files and update the `package` line to match your project.
