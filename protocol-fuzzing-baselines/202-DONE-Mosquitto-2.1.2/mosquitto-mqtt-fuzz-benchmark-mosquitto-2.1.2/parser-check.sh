#!/usr/bin/env bash
set -euo pipefail

PACKAGE_DIR=$(cd "$(dirname "$0")" && pwd)
TEMP_DIR=$(mktemp -d)
trap 'rm -rf -- "$TEMP_DIR"' EXIT

cc -std=c11 -Wall -Wextra -Werror \
  -I"$PACKAGE_DIR/test-stubs" \
  "$PACKAGE_DIR/mqtt_aflnet.c" "$PACKAGE_DIR/parser-test.c" \
  -o "$TEMP_DIR/mqtt-parser-test"
"$TEMP_DIR/mqtt-parser-test"
