#!/usr/bin/env bash
set -euo pipefail

# Only clear the disposable benchmark target's runtime data, never host services.
DATA_DIR=${INSPIRCD_DATA_DIR:-/home/ubuntu/experiments/inspircd-afl/run/data}
mkdir -p "${DATA_DIR}"
find "${DATA_DIR}" -mindepth 1 -maxdepth 1 -exec rm -rf -- {} +
