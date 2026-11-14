#!/usr/bin/env bash
set -euo pipefail
SEED_DIR=${SEED_DIR:-/opt/benchmark/seeds}
mkdir -p "$SEED_DIR"
mkdir -p /results
/opt/quiche/target/release/quiche-seedgen "$SEED_DIR/quic-v1-client-initial.bin"
python3 /opt/benchmark/validate_seeds.py "$SEED_DIR" > /results/quiche-seeds-validation.json
sha256sum "$SEED_DIR/quic-v1-client-initial.bin" > /results/quiche-seed.sha256
cat /results/quiche-seeds-validation.json
cat /results/quiche-seed.sha256
