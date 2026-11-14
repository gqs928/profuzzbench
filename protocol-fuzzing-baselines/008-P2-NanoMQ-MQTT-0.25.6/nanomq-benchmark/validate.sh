#!/usr/bin/env bash
set -euo pipefail

OUT=/work/results/preflight
mkdir -p /work/results
if [[ -e "${OUT}" ]] && [[ -n "$(find "${OUT}" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null)" ]]; then
  echo "Preflight results already exist: ${OUT}" >&2
  exit 2
fi
python3 /work/service_smoke.py "${OUT}/service-smoke"
bash /work/run.sh "${OUT}/aflnet-60s" 60s
test -s "${OUT}/aflnet-60s/aflnet-out/fuzzer_stats"
test -s "${OUT}/aflnet-60s/aflnet-out/ipsm.dot"
awk -F: '/^execs_done[[:space:]]*:/ { if ($2+0 > 0) ok=1 } END { exit !ok }' \
  "${OUT}/aflnet-60s/aflnet-out/fuzzer_stats"
IPSMDOT="${OUT}/aflnet-60s/aflnet-out/ipsm.dot"
for state_id in 0 2000 103 109 111 113; do
  if ! grep -Eq "^[[:space:]]*${state_id}[[:space:]]+\\[" "${IPSMDOT}"; then
    echo "Expected MQTT response state ${state_id} is missing from the IPSM graph" >&2
    exit 1
  fi
done
EDGE_COUNT="$(grep -c -- ' -> ' "${IPSMDOT}" || true)"
if [[ "${EDGE_COUNT}" -lt 5 ]]; then
  echo "Expected at least five MQTT response-state transitions, found ${EDGE_COUNT}" >&2
  exit 1
fi
printf 'ipsm_state_ids=0,2000,103,109,111,113\nipsm_edges=%s\n' "${EDGE_COUNT}" \
  > "${OUT}/state-summary.txt"
cp /work/build-lock.txt "${OUT}/build-lock.txt"
cp /work/results/build/image-id.txt "${OUT}/image-id.txt"
(cd "${OUT}" && find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS)
echo "PASS: MQTT 3.1.1/5.0 smoke and instrumented NanoMQ AFLNet feedback; evidence=${OUT}"
