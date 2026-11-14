#!/usr/bin/env bash
set -u

OUTDIR="${1:-/work/results/mqtt-30m}"
DURATION="${2:-1800s}"
STARTUP_WAIT_US="${AFLNET_STARTUP_US:-500000}"
if [[ -e "${OUTDIR}" ]] && [[ -n "$(find "${OUTDIR}" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null)" ]]; then
  echo "Output directory is nonempty: ${OUTDIR}. Choose a fresh path." >&2
  exit 2
fi
mkdir -p "${OUTDIR}"
test -s /work/results/build/image-id.txt
cp /work/results/build/image-id.txt "${OUTDIR}/image-id.txt"

date -u +%s > "${OUTDIR}/external-start-epoch.txt"
printf 'lifecycle_target=/opt/nanomq/nanomq (AFLNet-instrumented NanoMQ and NanoNNG C broker)\n' > "${OUTDIR}/run-method.txt"
printf 'broker=NanoMQ 0.25.6 persistent single node; MQTT response-state feedback enabled\n' >> "${OUTDIR}/run-method.txt"
printf 'instrumentation=afl-gcc compile instrumentation in NanoMQ and NanoNNG objects\n' >> "${OUTDIR}/run-method.txt"
printf 'server_startup_wait_us=%s (AFLNet -D)\n' "${STARTUP_WAIT_US}" >> "${OUTDIR}/run-method.txt"
set +e
timeout --signal=INT --kill-after=30s "${DURATION}" \
  env AFL_NO_UI=1 AFL_SKIP_BIN_CHECK=1 AFL_SKIP_CPUFREQ=1 AFL_NO_AFFINITY=1 \
  /opt/aflnet/afl-fuzz -d -i /work/seeds -x /work/mqtt.dict \
    -o "${OUTDIR}/aflnet-out" -N tcp://127.0.0.1/1883 -P MQTT \
    -E -q 3 -s 3 -R -K -D "${STARTUP_WAIT_US}" -W 100 -w 100000 -m none -t 5000+ \
    -- /work/target-start.sh >"${OUTDIR}/aflnet.log" 2>&1
FUZZER_STATUS=$?
set -e
date -u +%s > "${OUTDIR}/external-end-epoch.txt"
printf '%s\n' "${FUZZER_STATUS}" > "${OUTDIR}/wrapper-exit-code.txt"

if [[ -f "${OUTDIR}/aflnet-out/fuzzer_stats" ]]; then
  grep -E '^(execs_done|paths_total|variable_paths|stability|bitmap_cvg|unique_crashes|unique_hangs)[[:space:]]*:' \
    "${OUTDIR}/aflnet-out/fuzzer_stats" > "${OUTDIR}/fuzzer-summary.txt" || true
fi
if [[ "${FUZZER_STATUS}" -ne 124 && "${FUZZER_STATUS}" -ne 0 ]]; then
  echo "AFLNet exit status: ${FUZZER_STATUS}" >&2
  exit "${FUZZER_STATUS}"
fi
