#!/usr/bin/env bash
set -euo pipefail
PACKAGE_DIR=$(cd "$(dirname "$0")" && pwd)
CC=${CC:-cc}
TMPDIR=${TMPDIR:-/tmp}
output=$(mktemp "${TMPDIR%/}/imap-parser.XXXXXX")
trap 'rm -f "$output"' EXIT
"${CC}" -O2 -Wall -Wextra -Werror -I"${PACKAGE_DIR}/test-stubs" \
  "${PACKAGE_DIR}/parser-test.c" "${PACKAGE_DIR}/imap_aflnet.c" -o "${output}"
"${output}"
