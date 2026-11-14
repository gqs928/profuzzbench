#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd -- "$(dirname -- "$0")" && pwd)
"cc" -std=c11 -O2 -Wall -Wextra -Werror \
	-I"$ROOT/test-stubs" "$ROOT/nfs_aflnet.c" \
	"$ROOT/parser-test.c" -o /tmp/nfs-ganesha-parser-test
/tmp/nfs-ganesha-parser-test
rm -f /tmp/nfs-ganesha-parser-test
