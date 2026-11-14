#!/usr/bin/env bash
set -euo pipefail

mkdir -p /work/results/build
cp /work/build-evidence/* /work/results/build/
printf 'target_binary_version:\n' > /work/results/build/target-binary-version.txt
/opt/mediamtx/mediamtx --version >> /work/results/build/target-binary-version.txt 2>&1
printf 'target_help:\n' > /work/results/build/target-help.txt
/opt/mediamtx/mediamtx --help >> /work/results/build/target-help.txt 2>&1 || true
