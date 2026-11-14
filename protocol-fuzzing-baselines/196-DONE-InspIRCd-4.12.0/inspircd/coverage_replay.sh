#!/usr/bin/env bash
set -euo pipefail
exec python3 /workspace/coverage_replay.py "${1:?usage: coverage_replay.sh FUZZ_RESULT_DIR [SKIPCOUNT]}" "${2:-5}"
