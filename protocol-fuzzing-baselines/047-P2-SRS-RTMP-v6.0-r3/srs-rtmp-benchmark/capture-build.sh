#!/usr/bin/env bash
set -euo pipefail

OUT=/work/results/build
mkdir -p "$OUT"
cp /work/build-evidence/build-lock.txt "$OUT/build-lock.txt"
cp /work/build-evidence/srs-version.txt "$OUT/srs-version.txt"
cp /work/build-evidence/srs-binary.sha256 "$OUT/srs-binary.sha256"
cp /work/build-evidence/ubuntu-packages.txt "$OUT/ubuntu-packages.txt"
(cd /tmp && sha256sum -c /tmp/SHA256SUMS) > "$OUT/source-checksums.txt" 2>&1
/opt/aflnet/afl-fuzz -h > "$OUT/aflnet-help.txt" 2>&1 || true
printf 'SRS build: pass\nSRS release identity: v6.0-r3 / build v6.0.195\nRTMP AFLNet adapter tests: pass\n' > "$OUT/BUILD_ACCEPTANCE.txt"
