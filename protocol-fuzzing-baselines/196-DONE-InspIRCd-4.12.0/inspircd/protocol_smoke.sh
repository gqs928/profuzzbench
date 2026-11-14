#!/usr/bin/env bash
set -euo pipefail
exec python3 /workspace/protocol_smoke.py "${1:-/results/protocol-smoke}"
