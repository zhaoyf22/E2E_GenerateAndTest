# C++ CLI Pack Rules

- Use C++20, CMake 3.20+, and CTest; prefer GoogleTest for large projects, Catch2 for small ones.
- Test behavior through public APIs; do not test private members unless required by a contract.
- Use RAII and deterministic fixtures; avoid global mutable state and execution-order dependencies.
- Run ASan/UBSan/TSan in CI; a test that only passes without sanitizers is not enough.
- For CLI tools, assert exit codes, stdout, stderr, file side effects, and `--help` behavior.
- Use ApprovalTests.cpp for golden/snapshot output; store approved files in version control.
- Use FuzzTest/RapidCheck for parsers and invariants; use Mull for mutation feedback.
- Use testcontainers-native for Docker-backed integration tests (early-stage; build from source).
- Do not assert undefined behavior; fix the code or constrain the input.
