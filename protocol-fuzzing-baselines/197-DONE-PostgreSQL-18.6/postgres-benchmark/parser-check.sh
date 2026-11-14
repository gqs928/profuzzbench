#!/usr/bin/env bash
set -euo pipefail
PACKAGE_DIR=$(cd "$(dirname "$0")" && pwd)
TEMP_DIR=$(mktemp -d)
trap 'rm -rf "${TEMP_DIR}"' EXIT
cc -std=c11 -O2 -Wall -Wextra -Werror -I"${PACKAGE_DIR}/test-stubs" "${PACKAGE_DIR}/postgres_aflnet.c" "${PACKAGE_DIR}/parser-test.c" -o "${TEMP_DIR}/parser-test"
"${TEMP_DIR}/parser-test"
