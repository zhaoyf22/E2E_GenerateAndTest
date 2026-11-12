# UTBotCpp

- Repo: https://github.com/UnitTestBot/UTBotCpp
- Symbolic execution (KLEE) + GoogleTest generation for C/C++; reaches branches and maximizes coverage.
- Uses a patched CMake/Bear to build a compilation database, then KLEE.
- Distributed mainly for Ubuntu 20.04+; activity is slower than Java/Python tooling.
- Treat generated tests as a coverage baseline; review assertions and compile fixes.
