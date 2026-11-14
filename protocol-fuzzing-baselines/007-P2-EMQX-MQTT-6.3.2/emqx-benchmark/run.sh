#!/usr/bin/env bash
set -u

OUTDIR="${1:-/work/results/mqtt-30m}"
DURATION="${2:-1800s}"
mkdir -p "$(dirname "${OUTDIR}")"
if [[ -e "${OUTDIR}" ]] && [[ -n "$(find "${OUTDIR}" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null)" ]]; then
  echo "Output directory is nonempty: ${OUTDIR}. Choose a fresh path." >&2
  exit 2
fi
mkdir -p "${OUTDIR}"

REL=/tmp/emqx-release
mkdir -p "${REL}"
tar -xzf /opt/emqx-release/emqx-6.3.2.tar.gz -C "${REL}"
export EMQX_NODE__NAME='emqx@127.0.0.1'
export EMQX_NODE__COOKIE='emqx-baseline-local-cookie'
export EMQX_CONFIGS_PATH=/work
export ERL_FLAGS='+S 4:4 +SDcpu 2 +SDio 2'
export EMQX_LOG__CONSOLE__LEVEL=warning
export EMQX_LISTENERS__TCP__DEFAULT__BIND='127.0.0.1:1883'
export EMQX_LISTENERS__TCP__DEFAULT__ENABLE_AUTHN=false
export EMQX_LISTENERS__SSL__DEFAULT__ENABLE=false
export EMQX_LISTENERS__WS__DEFAULT__ENABLE=false
export EMQX_LISTENERS__WSS__DEFAULT__ENABLE=false
export EMQX_LISTENERS__QUIC__DEFAULT__ENABLE=false
export EMQX_DASHBOARD__LISTENERS__HTTP__ENABLE=false
export EMQX_DASHBOARD__LISTENERS__HTTP__BIND=0
export EMQX_DASHBOARD__LISTENERS__HTTPS__ENABLE=false
export EMQX_DASHBOARD__LISTENERS__HTTPS__BIND=0

"${REL}/bin/emqx" foreground --config /work/emqx.conf >"${OUTDIR}/emqx.log" 2>&1 &
BROKER_PID=$!
printf '%s\n' "${BROKER_PID}" > "${OUTDIR}/broker.pid"
cleanup() {
  kill "${BROKER_PID}" 2>/dev/null || true
  wait "${BROKER_PID}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

if ! python3 /work/wait_mqtt.py --host 127.0.0.1 --port 1883 --timeout 120; then
  echo "EMQX MQTT CONNECT/CONNACK readiness check failed" >&2
  cat "${OUTDIR}/emqx.log" >&2
  exit 1
fi
if ! kill -0 "${BROKER_PID}" 2>/dev/null; then
  echo "EMQX exited before AFLNet started" >&2
  cat "${OUTDIR}/emqx.log" >&2
  wait "${BROKER_PID}" || true
  exit 1
fi

date -u +%s > "${OUTDIR}/external-start-epoch.txt"
printf 'lifecycle_target=/work/aflnet-lifecycle (instrumented AFLNet forkserver stub)\n' > "${OUTDIR}/run-method.txt"
printf 'broker=EMQX 6.3.2 persistent single node; MQTT response-state feedback enabled\n' >> "${OUTDIR}/run-method.txt"
printf 'limitation=instrumentation and crash counters refer to lifecycle stub, not EMQX BEAM code\n' >> "${OUTDIR}/run-method.txt"
set +e
timeout --signal=INT --kill-after=30s "${DURATION}" \
  env AFL_NO_UI=1 AFL_SKIP_CPUFREQ=1 AFL_NO_AFFINITY=1 \
  /opt/aflnet/afl-fuzz -d -i /work/seeds -x /work/mqtt.dict \
    -o "${OUTDIR}/aflnet-out" -N tcp://127.0.0.1/1883 -P MQTT \
    -E -q 3 -s 3 -R -K -D 1000 -W 100 -w 100000 -m none -t 5000+ \
    -- /work/aflnet-lifecycle >"${OUTDIR}/aflnet.log" 2>&1
FUZZER_STATUS=$?
set -e
date -u +%s > "${OUTDIR}/external-end-epoch.txt"
printf '%s\n' "${FUZZER_STATUS}" > "${OUTDIR}/wrapper-exit-code.txt"

if ! kill -0 "${BROKER_PID}" 2>/dev/null; then
  echo "EMQX process exited during the AFLNet campaign" > "${OUTDIR}/broker-exit-observation.txt"
  wait "${BROKER_PID}" || printf 'exit_status=%s\n' "$?" >> "${OUTDIR}/broker-exit-observation.txt"
fi
if [[ -f "${OUTDIR}/aflnet-out/fuzzer_stats" ]]; then
  grep -E '^(execs_done|paths_total|variable_paths|stability|bitmap_cvg|unique_crashes|unique_hangs)[[:space:]]*:' \
    "${OUTDIR}/aflnet-out/fuzzer_stats" > "${OUTDIR}/fuzzer-summary.txt" || true
fi
if [[ "${FUZZER_STATUS}" -ne 124 && "${FUZZER_STATUS}" -ne 0 ]]; then
  echo "AFLNet exit status: ${FUZZER_STATUS}" >&2
  exit "${FUZZER_STATUS}"
fi
