// CLI11 argument-parsing test skeleton. Requires CLI11.
// Case: ${id}
// Expected: ${expected}

#include <CLI/CLI.hpp>
#include <gtest/gtest.h>

TEST(ScaffoldCli, DISABLED_Scaffold) {
  CLI::App app{"scaffold"};
  std::string input;
  app.add_option("--input", input);
  std::vector<std::string> args{"scaffold", "--input", "value"};
  app.parse(args);
  EXPECT_EQ(input, "value");
}
