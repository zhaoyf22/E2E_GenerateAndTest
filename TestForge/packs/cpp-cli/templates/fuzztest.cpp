// FuzzTest skeleton. Requires //fuzztest:fuzztest in Bazel or an installed FuzzTest.
// Case: ${id}
// Expected: ${expected}

#include "fuzztest/fuzztest.h"
#include "gtest/gtest.h"

static void scaffoldProperty(int value) {
  // Replace with the invariant the implementation must satisfy.
  (void)value;
}

FUZZ_TEST(ScaffoldFuzz, scaffoldProperty)
    .WithDomains(fuzztest::InRange(0, 1000));
