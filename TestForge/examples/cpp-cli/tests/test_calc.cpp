#include <gtest/gtest.h>

#include "calc.h"

TEST(Calc, AddsPositiveNumbers) {
  EXPECT_EQ(calc::add(2, 3), 5);
}

TEST(Calc, AddsNegativeNumbers) {
  EXPECT_EQ(calc::add(-2, -3), -5);
}

TEST(Calc, AddsZero) {
  EXPECT_EQ(calc::add(0, 0), 0);
}
