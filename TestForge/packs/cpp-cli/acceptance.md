# cpp-cli acceptance

```bash
cd <repo>/TestForge
python testforge.py init --stack cpp-cli --target <tmp> --dry-run
python -m unittest tests.test_pack_cpp -v
cmake -S examples/cpp-cli -B build-cpp -DCMAKE_BUILD_TYPE=Debug
cmake --build build-cpp -j
ctest --test-dir build-cpp --output-on-failure
python testforge.py validate --cases examples/cpp-cli/test-cases.sample.json --requirements examples/cpp-cli/requirements.json
python testforge.py scaffold --cases examples/cpp-cli/test-cases.sample.json --stack cli --out <tmp>/scaffold
```

Expected: init dry-run prints a config with one `cli` stack; pack test passes; CMake/CTest example passes when GoogleTest is available; validate exits 0; scaffold writes a disabled GoogleTest skeleton.
