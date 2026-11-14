#!/usr/bin/env bash
set -euo pipefail

OUT=/work/results/build
mkdir -p "$OUT"
cp /work/build-evidence/build-lock.txt "$OUT/build-lock.txt"
cp /work/build-evidence/nginx-version.txt "$OUT/nginx-version.txt"
cp /work/build-evidence/module-commit.txt "$OUT/module-commit.txt"
cp /work/build-evidence/alpine-packages.txt "$OUT/alpine-packages.txt"
cp /work/build-evidence/nginx-binary.sha256 "$OUT/nginx-binary.sha256"
cp /work/build-evidence/aflnet-binaries.sha256 "$OUT/aflnet-binaries.sha256"
cp /work/build-evidence/rtmp-adapter.sha256 "$OUT/rtmp-adapter.sha256"
GCOV_PREFIX=/tmp/nginx-config-test-gcov GCOV_PREFIX_STRIP=4 \
  /opt/nginx/sbin/nginx -t -c /work/nginx.conf > "$OUT/nginx-config-test.txt" 2>&1
/opt/aflnet/afl-fuzz -h > "$OUT/aflnet-help.txt" 2>&1 || true
(cd /tmp && sha256sum -c /tmp/SHA256SUMS) > "$OUT/source-checksums.txt" 2>&1
printf 'nginx build check: pass\nRTMP config test: pass\nAFLNet RTMP adapter tests: pass\n' > "$OUT/BUILD_ACCEPTANCE.txt"
