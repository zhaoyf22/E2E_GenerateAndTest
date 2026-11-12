# C++ CLI Example

Minimal CMake + GoogleTest C++ CLI example.

```bash
cd examples/cpp-cli
cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug
cmake --build build -j
ctest --test-dir build --output-on-failure
cd ../..
python testforge.py validate --cases examples/cpp-cli/test-cases.sample.json --requirements examples/cpp-cli/requirements.json
```

Requires CMake 3.20+, a C++20 compiler, and GoogleTest (`find_package(GTest)`). On Ubuntu: `sudo apt install libgtest-dev cmake`.
