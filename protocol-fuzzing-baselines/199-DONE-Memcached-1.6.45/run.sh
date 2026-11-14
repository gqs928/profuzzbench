#!/usr/bin/env bash
set -u

# AFLNet state-aware runner for Memcached ASCII/TCP.
# Usage: run.sh aflnet OUTDIR OPTIONS TIMEOUT SKIPCOUNT
FUZZER=${1:-aflnet}
OUTDIR=${2:-/results/memcached-run}
OPTIONS=${3:-}
TIMEOUT=${4:-30s}
SKIPCOUNT=${5:-5}

WORKDIR=${WORKDIR:-/home/ubuntu/experiments}
TARGET=${TARGET:-${WORKDIR}/memcached-fuzz/memcached}
INPUTS=${INPUTS:-${WORKDIR}/in-memcached}
DICT=${DICT:-${WORKDIR}/memcached.dict}
AFLNET=${AFLNET:-/home/ubuntu/aflnet}
FUZZER_BIN=${FUZZER_BIN:-${AFLNET}/afl-fuzz}
CLEAN_SCRIPT=${CLEAN_SCRIPT:-/workspace/clean.sh}
PORT=${PORT:-11211}

if [[ ${FUZZER} != aflnet ]]; then
  echo "This benchmark requires AFLNet with -P MEMCACHED state parsing; got: ${FUZZER}" >&2
  exit 2
fi
[[ -x ${FUZZER_BIN} ]] || { echo "AFLNet missing: ${FUZZER_BIN}" >&2; exit 2; }
[[ -x ${TARGET} ]] || { echo "Target missing: ${TARGET}" >&2; exit 2; }
[[ -d ${INPUTS} ]] || { echo "Seeds missing: ${INPUTS}" >&2; exit 2; }
[[ -f ${DICT} ]] || { echo "Dictionary missing: ${DICT}" >&2; exit 2; }
[[ -x ${CLEAN_SCRIPT} ]] || { echo "Cleanup script not executable: ${CLEAN_SCRIPT}" >&2; exit 2; }
if ! grep -q 'MEMCACHED' < <("${FUZZER_BIN}" -h 2>&1); then
  echo 'This afl-fuzz binary was not built with the MEMCACHED protocol parser.' >&2
  exit 2
fi
mkdir -p "$(dirname "${OUTDIR}")"
if [[ -e ${OUTDIR} ]] && [[ -n $(find "${OUTDIR}" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null) ]]; then
  echo "Output directory is nonempty: ${OUTDIR}. Choose a new path." >&2
  exit 2
fi

read -r -a EXTRA_OPTIONS <<< "${OPTIONS}"
export ASAN_OPTIONS=${ASAN_OPTIONS:-abort_on_error=1:symbolize=0:detect_leaks=0:detect_stack_use_after_return=1}
echo "Running AFLNet with MEMCACHED state feedback on ASCII/TCP ${PORT}; output=${OUTDIR}"

set +e
timeout --signal=INT --kill-after=10s "${TIMEOUT}" "${FUZZER_BIN}" -d -i "${INPUTS}" -x "${DICT}" -o "${OUTDIR}" -N "tcp://127.0.0.1/${PORT}" -P MEMCACHED -E -q 3 -s 3 -R -K -D 10000 -W 100 -w 100000 -m none -t 5000+ -c "${CLEAN_SCRIPT}" "${EXTRA_OPTIONS[@]}" "${TARGET}" -B ascii -p "${PORT}" -U 0 -t 1
STATUS=$?
set -e

echo "AFLNet exit status: ${STATUS}"
if [[ -f ${OUTDIR}/fuzzer_stats ]]; then
  grep -E '^(execs_done|paths_total|variable_paths|stability|bitmap_cvg|unique_crashes|unique_hangs)[[:space:]]*:' "${OUTDIR}/fuzzer_stats" || true
fi
# timeout returns 124 after delivering SIGINT when the requested duration ends.
if [[ ${STATUS} -eq 124 ]]; then exit 0; fi
exit "${STATUS}"
