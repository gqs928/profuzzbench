#!/usr/bin/env bash
set -euo pipefail
cp /work/build-evidence/build-lock.txt "${1:-/work/results/build-lock.txt}"
