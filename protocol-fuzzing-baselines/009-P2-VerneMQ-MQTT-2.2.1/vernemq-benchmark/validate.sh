#!/usr/bin/env bash
set -euo pipefail

OUT=/work/results/preflight/aflnet-60s-plugin-bootstrap
mkdir -p /work/results/preflight
/work/run.sh "${OUT}" 60s
test -s "${OUT}/aflnet-out/fuzzer_stats"
test -s "${OUT}/aflnet-out/ipsm.dot"
test -s "${OUT}/broker-health.txt"
awk -F: '/^execs_done[[:space:]]*:/ { if ($2+0 > 0) ok=1 } END { exit !ok }' "${OUT}/aflnet-out/fuzzer_stats"
IPSMDOT="${OUT}/aflnet-out/ipsm.dot"
for state_id in 0 2000 103 109 111 113; do
  if ! grep -Eq "^[[:space:]]*${state_id}[[:space:]]+\\[" "${IPSMDOT}"; then
    echo "Expected MQTT state ${state_id} missing from VerneMQ response graph" >&2
    exit 1
  fi
done
EDGE_COUNT="$(grep -c -- ' -> ' "${IPSMDOT}" || true)"
if [[ "${EDGE_COUNT}" -lt 5 ]]; then
  echo "Expected at least five MQTT response-state transitions, found ${EDGE_COUNT}" >&2
  exit 1
fi
printf 'ipsm_state_ids=0,2000,103,109,111,113\nipsm_edges=%s\n' "${EDGE_COUNT}" > /work/results/preflight/state-summary.txt
cp /work/build-lock.txt /work/results/preflight/build-lock.txt
cp /work/results/build/image-id.txt /work/results/preflight/image-id.txt
(cd /work/results/preflight && find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS)
echo "PASS: VerneMQ MQTT 3.1.1/5.0 smoke and AFLNet response-state feedback; evidence=/work/results/preflight"
