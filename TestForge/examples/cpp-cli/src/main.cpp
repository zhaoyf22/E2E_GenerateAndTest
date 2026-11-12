#include <cstdlib>
#include <iostream>

#include "calc.h"

int main(int argc, char** argv) {
  if (argc != 3) {
    std::cerr << "usage: app <a> <b>\n";
    return 2;
  }
  try {
    int a = std::stoi(argv[1]);
    int b = std::stoi(argv[2]);
    std::cout << calc::add(a, b) << "\n";
    return 0;
  } catch (const std::exception& exc) {
    std::cerr << "invalid integer: " << exc.what() << "\n";
    return 2;
  }
}
