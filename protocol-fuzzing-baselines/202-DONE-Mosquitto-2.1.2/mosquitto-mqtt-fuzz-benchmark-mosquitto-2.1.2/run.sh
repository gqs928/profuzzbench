#!/usr/bin/env bash
set -u

# Usage: run.sh OUTPUT_DIR TIMEOUT [AFL_OPTIONS]
OUTDIR=${1:-/results/mqtt-smoke}
TIMEOUT=${2:-60s}
OPTIONS=${3:-}
WORKDIR=${WORKDIR:-/home/ubuntu/experiments}
AFLNET=${AFLNET:-/home/ubuntu/aflnet}
FUZZER_BIN=${FUZZER_BIN:-${AFLNET}/afl-fuzz}
TARGET=${TARGET:-${WORKDIR}/mosquitto-afl/src/mosquitto}
INPUTS=${INPUTS:-${WORKDIR}/in-mqtt}
DICT=${DICT:-/workspace/mqtt.dict}
CLEAN_SCRIPT=${CLEAN_SCRIPT:-/workspace/clean.sh}
CONFIG=${CONFIG:-/workspace/mosquitto.conf}
PORT=${PORT:-1883}

[[ -x ${FUZZER_BIN} ]] || { echo "AFLNet missing: ${FUZZER_BIN}" >&2; exit 2; }
[[ -x ${TARGET} ]] || { echo "Instrumented broker missing: ${TARGET}" >&2; exit 2; }
[[ -d ${INPUTS} ]] || { echo "MQTT seed corpus missing: ${INPUTS}" >&2; exit 2; }
[[ -f ${DICT} ]] || { echo "MQTT dictionary missing: ${DICT}" >&2; exit 2; }
[[ -x ${CLEAN_SCRIPT} ]] || { echo "Cleanup script is not executable: ${CLEAN_SCRIPT}" >&2; exit 2; }
[[ -f ${CONFIG} ]] || { echo "Broker config missing: ${CONFIG}" >&2; exit 2; }
if ! grep -a -q 'MQTT' "$FUZZER_BIN"; then
  echo "AFLNet binary does not include the MQTT parser." >&2
  exit 2
fi
mkdir -p "$(dirname "${OUTDIR}")"
if [[ -e ${OUTDIR} ]] && [[ -n $(find "${OUTDIR}" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null) ]]; then
  echo "Output directory is nonempty: ${OUTDIR}. Choose a fresh path." >&2
  exit 2
fi

read -r -a EXTRA_OPTIONS <<< "${OPTIONS}"
export ASAN_OPTIONS=${ASAN_OPTIONS:-abort_on_error=1:symbolize=0:detect_leaks=0:detect_stack_use_after_return=1}
TARGET_ROOT=$(dirname "$(dirname "$TARGET")")
export LD_LIBRARY_PATH="$TARGET_ROOT/lib"
echo "Running AFLNet MQTT state feedback on loopback TCP/${PORT}; output=${OUTDIR}"

set +e
timeout --signal=INT --kill-after=10s "${TIMEOUT}" "${FUZZER_BIN}" \
  -d -i "${INPUTS}" -x "${DICT}" -o "${OUTDIR}" \
  -N "tcp://127.0.0.1/${PORT}" -P MQTT -E -q 3 -s 3 -R -K \
  -D 10000 -W 100 -w 100000 -m none -t 5000+ -c "${CLEAN_SCRIPT}" \
  "${EXTRA_OPTIONS[@]}" "${TARGET}" -c "${CONFIG}"
STATUS=$?
set -e

echo "AFLNet exit status: ${STATUS}"
if [[ -f ${OUTDIR}/fuzzer_stats ]]; then
  grep -E '^(execs_done|paths_total|variable_paths|stability|bitmap_cvg|unique_crashes|unique_hangs)[[:space:]]*:' "${OUTDIR}/fuzzer_stats" || true
fi
# timeout returns 124 after interrupting AFLNet at the requested end time.
if [[ ${STATUS} -eq 124 ]]; then exit 0; fi
exit "${STATUS}"
