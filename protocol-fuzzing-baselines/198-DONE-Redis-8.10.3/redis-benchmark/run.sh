#!/usr/bin/env bash
set -u

# Usage: run.sh OUTPUT_DIR TIMEOUT [AFL_OPTIONS]
OUTDIR=${1:-/results/redis-smoke}
TIMEOUT=${2:-60s}
OPTIONS=${3:-}
WORKDIR=${WORKDIR:-/home/ubuntu/experiments}
AFLNET=${AFLNET:-/home/ubuntu/aflnet}
FUZZER_BIN=${FUZZER_BIN:-${AFLNET}/afl-fuzz}
TARGET=${TARGET:-${WORKDIR}/redis-afl/src/redis-server}
INPUTS=${INPUTS:-${WORKDIR}/in-redis}
DICT=${DICT:-/workspace/redis.dict}
CLEAN_SCRIPT=${CLEAN_SCRIPT:-/workspace/clean.sh}
CONFIG=${CONFIG:-/workspace/redis.conf}
PORT=${PORT:-6379}

[[ -x ${FUZZER_BIN} ]] || { echo "AFLNet missing: ${FUZZER_BIN}" >&2; exit 2; }
[[ -x ${TARGET} ]] || { echo "Instrumented Redis server missing: ${TARGET}" >&2; exit 2; }
[[ -d ${INPUTS} ]] || { echo "RESP seed corpus missing: ${INPUTS}" >&2; exit 2; }
[[ -f ${DICT} ]] || { echo "RESP dictionary missing: ${DICT}" >&2; exit 2; }
[[ -x ${CLEAN_SCRIPT} ]] || { echo "Cleanup script is not executable: ${CLEAN_SCRIPT}" >&2; exit 2; }
[[ -f ${CONFIG} ]] || { echo "Redis config missing: ${CONFIG}" >&2; exit 2; }
if ! grep -a -q 'REDIS' "${FUZZER_BIN}"; then
  echo "AFLNet binary does not include the REDIS parser." >&2
  exit 2
fi
mkdir -p "$(dirname "${OUTDIR}")"
if [[ -e ${OUTDIR} ]] && [[ -n $(find "${OUTDIR}" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null) ]]; then
  echo "Output directory is nonempty: ${OUTDIR}. Choose a fresh path." >&2
  exit 2
fi

read -r -a EXTRA_OPTIONS <<< "${OPTIONS}"
export ASAN_OPTIONS=${ASAN_OPTIONS:-abort_on_error=1:symbolize=0:detect_leaks=0:detect_stack_use_after_return=1}
echo "Running AFLNet RESP2/RESP3 state feedback on loopback TCP/${PORT}; output=${OUTDIR}"

set +e
timeout --signal=INT --kill-after=10s "${TIMEOUT}" "${FUZZER_BIN}" \
  -d -i "${INPUTS}" -x "${DICT}" -o "${OUTDIR}" \
  -N "tcp://127.0.0.1/${PORT}" -P REDIS -E -q 3 -s 3 -R -K \
  -D 10000 -W 100 -w 100000 -m none -t 5000+ -c "${CLEAN_SCRIPT}" \
  "${EXTRA_OPTIONS[@]}" "${TARGET}" "${CONFIG}"
STATUS=$?
set -e

echo "AFLNet exit status: ${STATUS}"
if [[ -f ${OUTDIR}/fuzzer_stats ]]; then
  grep -E '^(execs_done|paths_total|variable_paths|stability|bitmap_cvg|unique_crashes|unique_hangs)[[:space:]]*:' "${OUTDIR}/fuzzer_stats" || true
fi
if [[ -s ${OUTDIR}/plot_data && -f /workspace/plot_data_to_csv.py ]]; then
  if ! python3 /workspace/plot_data_to_csv.py \
    "${OUTDIR}/plot_data" "${OUTDIR}/coverage-timeseries.csv"; then
    echo "AFLNet exited before its first plot sample; no time-series CSV was emitted."
  fi
fi
if [[ ${STATUS} -eq 124 ]]; then exit 0; fi
exit "${STATUS}"
