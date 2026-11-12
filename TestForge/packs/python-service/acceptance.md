# python-service acceptance

```bash
cd <repo>/TestForge
python testforge.py init --stack python-service --target <tmp> --dry-run
python -m unittest tests.test_pack_python -v
python -m pytest examples/python-service/tests -q
python testforge.py validate --cases examples/python-service/test-cases.sample.json --requirements examples/python-service/requirements.json
python testforge.py scaffold --cases examples/python-service/test-cases.sample.json --stack api --out <tmp>/scaffold
```

Expected: init dry-run prints a config with one `api` stack; pack test passes; example pytest passes; validate exits 0; scaffold writes a skipped pytest skeleton.
