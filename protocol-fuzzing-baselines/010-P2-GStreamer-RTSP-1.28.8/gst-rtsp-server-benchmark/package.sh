#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="${ROOT}/results/rtsp-30m"
DELIVERABLES="${ROOT}/../deliverables"
ZIP="${DELIVERABLES}/GStreamer-RTSP-1.28.8.zip"

test -s "${ROOT}/results/ACCEPTANCE.md"
test -s "${ROOT}/results/build/build-lock.txt"
test -s "${ROOT}/results/build/image-id.txt"
test -s "${ROOT}/results/build/target-instrumentation-symbol-count.txt"
test -s "${ROOT}/results/preflight-live/SHA256SUMS"
test -s "${ROOT}/results/preflight-live/aflnet-60s-final6/aflnet-out/ipsm.dot"
grep -q ' -> ' "${ROOT}/results/preflight-live/aflnet-60s-final6/aflnet-out/ipsm.dot"
test -s "${OUT}/wrapper-exit-code.txt"
test "$(cat "${OUT}/wrapper-exit-code.txt")" -eq 124
test -s "${OUT}/fuzzer-exit-code.txt"
test -s "${OUT}/aflnet-out/fuzzer_stats"
test -s "${OUT}/aflnet-out/ipsm.dot"
test -s "${OUT}/post-smoke/rtsp-smoke.json"
test "$(cat "${OUT}/post-smoke/health.txt")" = 'rtsp_health=pass_after_campaign'
FUZZ_START="$(awk -F: '/^start_time[[:space:]]*:/ {gsub(/[[:space:]]/,"",$2); print $2}' "${OUT}/aflnet-out/fuzzer_stats")"
FUZZ_END="$(awk -F: '/^last_update[[:space:]]*:/ {gsub(/[[:space:]]/,"",$2); print $2}' "${OUT}/aflnet-out/fuzzer_stats")"
FUZZ_SECONDS=$((FUZZ_END - FUZZ_START))
test "${FUZZ_SECONDS}" -ge 1799
START="$(cat "${OUT}/external-start-epoch.txt")"
END="$(cat "${OUT}/external-end-epoch.txt")"
ELAPSED=$((END - START))
test "${ELAPSED}" -ge 1799
printf 'observed_elapsed_seconds=%s\n' "${ELAPSED}" > "${OUT}/elapsed-seconds.txt"

cd "${ROOT}"
find results -type f ! -name SHA256SUMS ! -path '*/__pycache__/*' ! -name '*.pyc' -print0 | sort -z | xargs -0 sha256sum > results/SHA256SUMS
mkdir -p "${DELIVERABLES}"
rm -f "${ZIP}"
cd "${ROOT}/.."
zip -qr "${ZIP}" gst-rtsp-server-benchmark -x 'gst-rtsp-server-benchmark/**/__pycache__/*' 'gst-rtsp-server-benchmark/**/*.pyc'
cd "${DELIVERABLES}"
sha256sum "$(basename "${ZIP}")" > "$(basename "${ZIP}").sha256"
unzip -tq "${ZIP}"
sha256sum -c "${ZIP}.sha256"
printf 'packaged=%s\nwall_seconds=%s\nfuzzer_seconds=%s\n' "${ZIP}" "${ELAPSED}" "${FUZZ_SECONDS}"
