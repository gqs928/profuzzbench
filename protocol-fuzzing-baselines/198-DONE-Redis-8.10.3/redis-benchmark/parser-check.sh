#!/usr/bin/env bash
set -euo pipefail
PACKAGE_DIR=$(cd "$(dirname "$0")" && pwd)
TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT
cc -O2 -Wall -Wextra -Werror -I"${PACKAGE_DIR}/test-stubs" \
  "${PACKAGE_DIR}/redis_aflnet.c" "${PACKAGE_DIR}/parser-test.c" \
  -o "${TMPDIR}/parser-test"
"${TMPDIR}/parser-test"
