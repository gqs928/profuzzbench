#!/usr/bin/env bash
set -Eeuo pipefail

WORK=/tmp/ergo-data/target
rm -rf "$WORK"
mkdir -p "$WORK"
cd "$WORK"
exec /opt/ergo-afl/ergo "$@"
