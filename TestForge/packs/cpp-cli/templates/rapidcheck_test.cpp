// RapidCheck property-based test skeleton. Requires rapidcheck.
// Case: ${id}
// Expected: ${expected}

#include <rapidcheck.h>

int main() {
  bool ok = rc::check("scaffold property", [](int value) {
    RC_ASSERT(value == value);
  });
  return ok ? 0 : 1;
}
