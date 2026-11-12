# python-service acceptance

```bash
cd <repo>/TestForge
python testforge.py init --profile python-service --target <tmp> --dry-run
python testforge.py init --profile python-service --target <tmp>
python -m unittest tests.test_pack_python -v
python -m pytest examples/python-service/tests -q
python testforge.py validate --cases examples/python-service/test-cases.sample.json --requirements examples/python-service/requirements.json
python testforge.py scaffold --cases examples/python-service/test-cases.sample.json --stack api --config <tmp>/testforge.config.json --out <tmp>/scaffold
```

Expected: init dry-run prints a config with one `api` stack (the `python-service` profile); pack test passes; example pytest passes; validate exits 0; scaffold writes a skipped pytest skeleton.

Report-artifact check (when mutmut is installed): `python testforge.py run --manifest .testforge/run-manifest.json --with-reports` runs `mutmut run && mutmut export-cicd-stats`, which writes `mutants/mutmut-cicd-stats.json`; `gate` reads that file through the `mutmut` parser and computes `killed / (killed + survived)`.
