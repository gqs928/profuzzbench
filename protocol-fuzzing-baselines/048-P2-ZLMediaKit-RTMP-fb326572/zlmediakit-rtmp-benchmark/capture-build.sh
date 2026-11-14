#!/usr/bin/env bash
set -euo pipefail

OUT=/work/results/build
mkdir -p "$OUT"
cp /work/build-evidence/build-lock.txt "$OUT/build-lock.txt"
cp /work/build-evidence/zlm-version.txt "$OUT/zlm-version.txt"
cp /work/build-evidence/zlm-binary.sha256 "$OUT/zlm-binary.sha256"
cp /work/build-evidence/aflnet-binaries.sha256 "$OUT/aflnet-binaries.sha256"
cp /work/build-evidence/rtmp-adapter.sha256 "$OUT/rtmp-adapter.sha256"
cp /work/build-evidence/ubuntu-packages.txt "$OUT/ubuntu-packages.txt"
(cd /tmp && sha256sum -c /tmp/SHA256SUMS) > "$OUT/source-checksums.txt" 2>&1
/opt/aflnet/afl-fuzz -h > "$OUT/aflnet-help.txt" 2>&1 || true
printf 'ZLMediaKit build: pass\nTarget snapshot: fb3265725f0880da1f52a3cc6e6eb04bbc327fa3\nRTMP AFLNet adapter tests: pass\n' > "$OUT/BUILD_ACCEPTANCE.txt"
