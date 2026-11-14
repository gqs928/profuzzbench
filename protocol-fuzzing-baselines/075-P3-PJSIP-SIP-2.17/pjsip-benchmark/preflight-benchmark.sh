#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")" && pwd)
duration=${1:-60}
label=${2:-pjsip-preflight-60s-$(date -u +%Y%m%d-%H%M%S)}
"$root/run-benchmark.sh" "$duration" "$label"
