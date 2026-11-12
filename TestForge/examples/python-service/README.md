# Python Service Example

Minimal Python service with pytest, coverage, and TestForge cases.

```bash
cd examples/python-service
python -m pytest -q
python ../../testforge.py validate --cases test-cases.sample.json --requirements requirements.json
python ../../testforge.py export --cases test-cases.sample.json --format testrail --out testrail.csv
```
