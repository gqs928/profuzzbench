#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
./run-benchmark.sh /results/google-quiche-preflight-60s-20261113 60s
