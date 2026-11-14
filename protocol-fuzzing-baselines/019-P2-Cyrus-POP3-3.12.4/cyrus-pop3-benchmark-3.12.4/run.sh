#!/usr/bin/env bash
set -u

# Usage: run.sh OUTPUT_DIR TIMEOUT [AFL_OPTIONS]
OUTDIR=${1:-/results/pop3-smoke}
TIMEOUT=${2:-60s}
OPTIONS=${3:-}
WORKDIR=${WORKDIR:-/home/ubuntu/experiments}
AFLNET=${AFLNET:-/home/ubuntu/aflnet}
FUZZER_BIN=${FUZZER_BIN:-${AFLNET}/afl-fuzz}
INPUTS=${INPUTS:-${WORKDIR}/in-pop3}
DICT=${DICT:-/workspace/pop3.dict}
TARGET=${TARGET:-${WORKDIR}/start_server_afl}
CYRUS_PREFIX=${CYRUS_PREFIX:-${WORKDIR}/cyrus-afl}
PORT=${POP3_PORT:-1110}

[[ -x ${FUZZER_BIN} ]] || { echo "AFLNet missing: ${FUZZER_BIN}" >&2; exit 2; }
[[ -d ${INPUTS} ]] || { echo "POP3 seed corpus missing: ${INPUTS}" >&2; exit 2; }
[[ -f ${DICT} ]] || { echo "POP3 dictionary missing: ${DICT}" >&2; exit 2; }
[[ -x /workspace/restore-state.sh ]] || { echo "Cyrus state restore script missing" >&2; exit 2; }
[[ -x ${TARGET} ]] || { echo "Cyrus AFL target launcher missing: ${TARGET}" >&2; exit 2; }
grep -a -q 'POP3' "${FUZZER_BIN}" || { echo "AFLNet binary does not contain the POP3 parser" >&2; exit 2; }
if [[ -e ${OUTDIR} ]] && [[ -n $(find "${OUTDIR}" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null) ]]; then
  echo "Output directory is nonempty: ${OUTDIR}" >&2
  exit 2
fi
mkdir -p "$(dirname "${OUTDIR}")"
read -r -a EXTRA_OPTIONS <<< "${OPTIONS}"
export CYRUS_PREFIX
export PATH="${CYRUS_PREFIX}/bin:${CYRUS_PREFIX}/sbin:${CYRUS_PREFIX}/libexec:${PATH}"
export LD_LIBRARY_PATH="${CYRUS_PREFIX}/lib${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"
export ASAN_OPTIONS=${ASAN_OPTIONS:-abort_on_error=1:symbolize=0:detect_leaks=0:detect_stack_use_after_return=1}
echo "Running AFLNet POP3 state feedback on isolated loopback TCP/${PORT}; output=${OUTDIR}"
set +e
timeout --signal=INT --kill-after=10s "${TIMEOUT}" "${FUZZER_BIN}" -d \
  -i "${INPUTS}" -x "${DICT}" -o "${OUTDIR}" \
  -N "tcp://127.0.0.1/${PORT}" -P POP3 -E -q 3 -s 3 -R -K \
  -D 10000 -W 100 -w 100000 -m none -t 5000+ -c /workspace/clean.sh \
  "${EXTRA_OPTIONS[@]}" "${TARGET}"
runner_rc=$?
set -e
echo "AFLNet exit status: ${runner_rc}"
if [[ -f ${OUTDIR}/fuzzer_stats ]]; then
  grep -E '^(execs_done|paths_total|variable_paths|stability|bitmap_cvg|unique_crashes|unique_hangs)[[:space:]]*:' "${OUTDIR}/fuzzer_stats" || true
fi
if [[ ${runner_rc} -eq 124 ]]; then exit 0; fi
exit "${runner_rc}"
