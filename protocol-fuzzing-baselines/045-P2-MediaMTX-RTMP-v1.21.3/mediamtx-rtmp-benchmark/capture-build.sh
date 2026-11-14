#!/usr/bin/env bash
set -euo pipefail

mkdir -p /work/results/build
cp /work/build-evidence/* /work/results/build/
/opt/mediamtx/mediamtx --version > /work/results/build/target-version.txt 2>&1
/opt/aflnet/afl-fuzz -h > /work/results/build/aflnet-help.txt 2>&1 || true
cp /work/source-lock.json /work/results/build/source-lock.json
