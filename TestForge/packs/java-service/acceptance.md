# java-service acceptance

```bash
cd <repo>/TestForge
python testforge.py init --stack java-service --target <tmp> --dry-run
python -m unittest tests.test_pack_java -v
mvn -q -f examples/java-service/pom.xml test
python testforge.py validate --cases examples/java-service/test-cases.sample.json --requirements examples/java-service/requirements.json
python testforge.py scaffold --cases examples/java-service/test-cases.sample.json --stack svc --out <tmp>/scaffold
```

Expected: init dry-run prints a config with one `svc` stack; pack test passes; Maven example passes; validate exits 0; scaffold writes a disabled JUnit 5 test.
