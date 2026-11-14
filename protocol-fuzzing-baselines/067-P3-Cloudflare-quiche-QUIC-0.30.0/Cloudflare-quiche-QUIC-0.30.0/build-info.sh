#!/usr/bin/env bash
set -euo pipefail
mkdir -p /results/build-logs
aflnet_map_pow2=$(awk '/^#define MAP_SIZE_POW2/ {print $3; exit}' /opt/aflnet/config.h | tr -d '\r')
aflnet_map_bytes=$((1 << aflnet_map_pow2))
cat <<EOF
$(rustc --version --verbose)
$(cargo --version)
$(cargo afl --version)
aflnet_version=2.56b (commit 0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732)
aflnet_map_size=${aflnet_map_bytes}
target_instrumented_map_size=$(AFL_DUMP_MAP_SIZE=1 "$QUICHE_SERVER" --help 2>/dev/null || true)
forkserver_compatibility=AFL_OLD_FORKSERVER=1; AFLNet 2.56b vanilla forkserver
$(grep -m1 '^version' /opt/quiche/Cargo.toml)
$(sha256sum /opt/quiche/target/release/quiche-server)
$(sha256sum /opt/aflnet/afl-fuzz)
EOF
python3 - <<'PY'
from pathlib import Path
import hashlib, json
p=Path('/opt/quiche/Cargo.lock')
print(json.dumps({'cargo_lock': str(p), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'bytes': p.stat().st_size}, indent=2))
PY
cp /opt/quiche/Cargo.lock /results/build-logs/quiche-Cargo.lock
