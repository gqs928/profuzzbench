#!/usr/bin/env bash
set -euo pipefail
OUT="${1:-/work/build-evidence/runtime.txt}"
{
  printf 'date_utc='; date -u +%FT%TZ
  printf 'uname='; uname -a
  printf 'target_version='; /opt/opensmtpd/sbin/smtpd -h 2>&1 | head -1 || true
  printf 'aflnet_version='; /opt/aflnet/afl-fuzz -h 2>&1 | head -1 || true
  printf 'target_binary='; sha256sum /opt/opensmtpd/sbin/smtpd
} > "$OUT"
