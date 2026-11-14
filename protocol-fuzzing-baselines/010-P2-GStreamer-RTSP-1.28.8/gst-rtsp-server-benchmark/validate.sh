#!/usr/bin/env bash
set -euo pipefail

PREFLIGHT_ROOT="${PREFLIGHT_ROOT:-/work/results/preflight}"
OUT="${PREFLIGHT_OUT:-${PREFLIGHT_ROOT}/aflnet-60s}"
mkdir -p "${PREFLIGHT_ROOT}"
/work/run.sh "${OUT}" 60s
test -s "${OUT}/aflnet-out/fuzzer_stats"
test -s "${OUT}/aflnet-out/ipsm.dot"
test -s "${OUT}/post-smoke/rtsp-smoke.json"
awk -F: '/^execs_done[[:space:]]*:/ { if ($2+0 > 0) ok=1 } END { exit !ok }' "${OUT}/aflnet-out/fuzzer_stats"
grep -q '200' "${OUT}/aflnet-out/ipsm.dot"
grep -q -- ' -> ' "${OUT}/aflnet-out/ipsm.dot"
cp /work/build-evidence/build-lock.txt "${PREFLIGHT_ROOT}/build-lock.txt"
cp /work/build-evidence/version.txt "${PREFLIGHT_ROOT}/target-versions.txt"
(cd "${PREFLIGHT_ROOT}" && find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS)
echo "PASS: RTSP/TCP smoke and GStreamer AFLNet response-state preflight; inspect bitmap separately before treating it as target coverage; evidence=${PREFLIGHT_ROOT}"
