# cpp-cli acceptance

```bash
cd <repo>/TestForge
python testforge.py init --profile cpp-cli --target <tmp> --dry-run
python testforge.py init --profile cpp-cli --target <tmp>
python -m unittest tests.test_pack_cpp -v
cmake -S examples/cpp-cli -B build-cpp -DCMAKE_BUILD_TYPE=Debug
cmake --build build-cpp -j
ctest --test-dir build-cpp --output-on-failure
python testforge.py validate --cases examples/cpp-cli/test-cases.sample.json --requirements examples/cpp-cli/requirements.json
python testforge.py scaffold --cases examples/cpp-cli/test-cases.sample.json --stack cli --config <tmp>/testforge.config.json --out <tmp>/scaffold
```

Expected: init dry-run prints a config with one `cli` stack (the `cpp-cli` profile); pack test passes; CMake/CTest example passes when GoogleTest is available; validate exits 0; scaffold writes a disabled GoogleTest skeleton.

Report-artifact check (when lcov/Mull are installed):

- Coverage: the pack expects `build/coverage.info` and parses it with `lcov`.
- Mutation: `mull-runner build/tests --reporters Elements --report-dir build/mull-report --report-name mutation` writes `build/mull-report/mutation.json`; `gate` reads it with the `json` parser and computes killed/survived from the Elements report. Replace `build/tests` with the path to your built test binary.
