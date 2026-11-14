#!/usr/bin/env bash
set -euo pipefail
export CYRUS_PREFIX=${CYRUS_PREFIX:-/home/ubuntu/experiments/cyrus-reference}
exec /home/ubuntu/experiments/start_server_reference
