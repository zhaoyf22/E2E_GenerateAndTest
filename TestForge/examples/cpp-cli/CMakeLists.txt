cmake_minimum_required(VERSION 3.20)
project(testforge_cpp_example CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_library(calc src/calc.cpp)
target_include_directories(calc PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/src)

add_executable(app src/main.cpp)
target_link_libraries(app PRIVATE calc)

enable_testing()
find_package(GTest REQUIRED)
add_executable(calc_tests tests/test_calc.cpp)
target_link_libraries(calc_tests PRIVATE calc GTest::gtest_main)
include(GoogleTest)
gtest_discover_tests(calc_tests)
