#!/usr/bin/env bash
set -euo pipefail

TARGET=""
PROFILE="platform"
WITH_CI=""
FORCE=""

usage() {
  echo "Usage: $0 --target <project> [--profile platform|service|cli|frontend|backend] [--with-ci] [--force]"
  exit 2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target) TARGET="$2"; shift 2 ;;
    --profile) PROFILE="$2"; shift 2 ;;
    --with-ci) WITH_CI="--with-ci"; shift ;;
    --force) FORCE="--force"; shift ;;
    *) usage ;;
  esac
done

if [[ -z "$TARGET" ]]; then usage; fi

SUITE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLI="$SUITE_ROOT/testforge.py"

if [[ ! -f "$CLI" ]]; then
  echo "testforge.py not found at $CLI" >&2
  exit 1
fi

echo "Installing TestForge into $TARGET (profile=$PROFILE)..."
python3 "$CLI" init --target "$TARGET" --profile "$PROFILE" $WITH_CI $FORCE

echo ""
echo "Next:"
echo "  cd $TARGET"
echo "  python3 testforge/testforge.py doctor"
echo "  python3 testforge/testforge.py pack"
