#!/usr/bin/env bash
set -euo pipefail
cat /opt/benchmark/build-info.txt
python3 /opt/benchmark/validate_seeds.py /opt/benchmark/seeds
