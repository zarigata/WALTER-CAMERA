#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

FAILED=0

python -m interactive_video_booth.main --stage 0 || FAILED=1
python -m interactive_video_booth.main --stage 1 || FAILED=1

if [ "$FAILED" -eq 0 ]; then
  echo "SMOKE TESTS: STAGE0 OK, STAGE1 OK -> PASS"
  exit 0
else
  echo "SMOKE TESTS: FAIL" >&2
  exit 1
fi
