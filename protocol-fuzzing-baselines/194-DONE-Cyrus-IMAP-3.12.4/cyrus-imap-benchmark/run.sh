#!/usr/bin/env bash
set -u

# Usage: run.sh OUTPUT_DIR TIMEOUT [AFL_OPTIONS]
OUTDIR=${1:-/results/imap-smoke}
TIMEOUT=${2:-60s}
OPTIONS=${3:-}
WORKDIR=${WORKDIR:-/home/ubuntu/experiments}
AFLNET=${AFLNET:-/home/ubuntu/aflnet}
FUZZER_BIN=${FUZZER_BIN:-${AFLNET}/afl-fuzz}
TARGET=${TARGET:-}
INPUTS=${INPUTS:-${WORKDIR}/in-imap}
DICT=${DICT:-/workspace/imap.dict}
CLEAN_SCRIPT=${CLEAN_SCRIPT:-/workspace/clean.sh}
RESET_SCRIPT=${RESET_SCRIPT:-/workspace/reset-state.sh}
CYRUS_PREFIX=${CYRUS_PREFIX:-${WORKDIR}/cyrus-afl}
PORT=${IMAP_PORT:-1143}

[[ -x ${FUZZER_BIN} ]] || { echo "AFLNet missing: ${FUZZER_BIN}" >&2; exit 2; }
[[ -d ${INPUTS} ]] || { echo "IMAP seed corpus missing: ${INPUTS}" >&2; exit 2; }
[[ -f ${DICT} ]] || { echo "IMAP dictionary missing: ${DICT}" >&2; exit 2; }
[[ -x ${CLEAN_SCRIPT} ]] || { echo "Cleanup script missing: ${CLEAN_SCRIPT}" >&2; exit 2; }
[[ -x ${RESET_SCRIPT} ]] || { echo "State reset script missing: ${RESET_SCRIPT}" >&2; exit 2; }
grep -a -q 'IMAP' "${FUZZER_BIN}" || { echo "AFLNet binary does not include the IMAP parser." >&2; exit 2; }
mkdir -p "$(dirname "${OUTDIR}")"
if [[ -e ${OUTDIR} ]] && [[ -n $(find "${OUTDIR}" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null) ]]; then
  echo "Output directory is nonempty: ${OUTDIR}. Choose a fresh path." >&2
  exit 2
fi

read -r -a EXTRA_OPTIONS <<< "${OPTIONS}"
export CYRUS_PREFIX
export PATH="${CYRUS_PREFIX}/bin:${CYRUS_PREFIX}/sbin:${CYRUS_PREFIX}/libexec:${PATH}"
export LD_LIBRARY_PATH="${CYRUS_PREFIX}/lib${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"
export ASAN_OPTIONS=${ASAN_OPTIONS:-abort_on_error=1:symbolize=0:detect_leaks=0:detect_stack_use_after_return=1}
if [[ -z ${TARGET:-} ]]; then
  TARGET=${WORKDIR}/start_server_afl
  AFL_USE_ASAN=1 "${AFLNET}/afl-clang-fast" -O1 -g \
    -fno-omit-frame-pointer /workspace/start_server.c -o "${TARGET}"
fi
[[ -x ${TARGET} ]] || { echo "IMAP target launcher missing: ${TARGET}" >&2; exit 2; }
trap '"${RESET_SCRIPT}"' EXIT
echo "Running AFLNet IMAP state feedback on isolated loopback TCP/${PORT}; output=${OUTDIR}"

set +e
timeout --signal=INT --kill-after=10s "${TIMEOUT}" "${FUZZER_BIN}" -d -i "${INPUTS}" -x "${DICT}" -o "${OUTDIR}" -N "tcp://127.0.0.1/${PORT}" -P IMAP -E -q 3 -s 3 -R -K -D 10000 -W 100 -w 100000 -m none -t 5000+ -c "${CLEAN_SCRIPT}" "${EXTRA_OPTIONS[@]}" "${TARGET}"
STATUS=$?
set -e

echo "AFLNet exit status: ${STATUS}"
if [[ -f ${OUTDIR}/fuzzer_stats ]]; then
  grep -E '^(execs_done|paths_total|variable_paths|stability|bitmap_cvg|unique_crashes|unique_hangs)[[:space:]]*:' "${OUTDIR}/fuzzer_stats" || true
fi
if [[ ${STATUS} -eq 124 ]]; then exit 0; fi
exit "${STATUS}"
