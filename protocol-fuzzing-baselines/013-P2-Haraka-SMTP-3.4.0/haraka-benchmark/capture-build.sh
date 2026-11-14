#!/usr/bin/env bash
set -euo pipefail
OUT="${1:-/work/build-evidence/runtime.txt}"
{
  printf 'date_utc='; date -u +%FT%TZ
  printf 'uname='; uname -a
  printf 'node='; node --version
  printf 'npm='; npm --version
  printf 'target='; node -p "require('/src/Haraka/package.json').version"
  printf 'npm_lock='; sha256sum /src/Haraka/package-lock.json
  printf 'afl_fuzz='; /opt/aflnet/afl-fuzz -h 2>&1 | head -1 || true
} > "$OUT"
