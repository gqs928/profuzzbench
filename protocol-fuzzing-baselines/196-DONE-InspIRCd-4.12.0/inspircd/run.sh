#!/usr/bin/env bash
set -u

# Usage: run.sh aflnet OUTPUT_DIR OPTIONS TIMEOUT
FUZZER=${1:-aflnet}
OUTDIR=${2:-/results/irc-smoke}
OPTIONS=${3:-}
TIMEOUT=${4:-60s}

WORKDIR=${WORKDIR:-/home/ubuntu/experiments}
AFLNET=${AFLNET:-/home/ubuntu/aflnet}
FUZZER_BIN=${FUZZER_BIN:-${AFLNET}/afl-fuzz}
TARGET=${TARGET:-${WORKDIR}/inspircd-afl/run/bin/inspircd}
CONFIG=${CONFIG:-${WORKDIR}/inspircd-afl/run/conf/inspircd.conf}
INPUTS=${INPUTS:-${WORKDIR}/in-irc}
DICT=${DICT:-${WORKDIR}/irc.dict}
PORT=${PORT:-6667}
CLEAN_SCRIPT=${CLEAN_SCRIPT:-/workspace/clean.sh}

if [[ ${FUZZER} != aflnet ]]; then
  echo "This benchmark requires the patched AFLNet IRC parser; got: ${FUZZER}" >&2
  exit 2
fi
[[ -x ${FUZZER_BIN} && -x ${TARGET} && -f ${CONFIG} && -d ${INPUTS} && -f ${DICT} ]] || {
  echo "Missing AFLNet, target, config, seed corpus, or dictionary." >&2
  exit 2
}
[[ -x ${CLEAN_SCRIPT} ]] || { echo "Cleanup script is not executable: ${CLEAN_SCRIPT}" >&2; exit 2; }
"${FUZZER_BIN}" -h 2>&1 | grep -q 'IRC' || {
  echo 'afl-fuzz was not built with the IRC protocol adapter.' >&2
  exit 2
}
mkdir -p "$(dirname "${OUTDIR}")"
if [[ -e ${OUTDIR} ]] && [[ -n $(find "${OUTDIR}" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null) ]]; then
  echo "Output directory is not empty: ${OUTDIR}" >&2
  exit 2
fi

EXTRA_OPTIONS=()
if [[ -n ${OPTIONS} ]]; then
  read -r -a EXTRA_OPTIONS <<< "${OPTIONS}"
fi
export ASAN_OPTIONS=${ASAN_OPTIONS:-abort_on_error=1:symbolize=0:detect_leaks=0:detect_stack_use_after_return=1}
export INSPIRCD_DATA_DIR=${WORKDIR}/inspircd-afl/run/data
echo "Running AFLNet with IRC state feedback on TCP/${PORT}; output=${OUTDIR}"

set +e
timeout --signal=INT --kill-after=10s "${TIMEOUT}" \
  "${FUZZER_BIN}" -d -i "${INPUTS}" -x "${DICT}" -o "${OUTDIR}" \
  -N "tcp://127.0.0.1/${PORT}" -P IRC -E -q 3 -s 3 -R -K \
  -D 100000 -W 100 -w 100000 -m none -t 5000+ -c "${CLEAN_SCRIPT}" \
  "${EXTRA_OPTIONS[@]}" \
  "${TARGET}" -F -L -P -c "${CONFIG}"
STATUS=$?
set -e

echo "AFLNet exit status: ${STATUS}"
if [[ -f ${OUTDIR}/fuzzer_stats ]]; then
  grep -E '^(execs_done|paths_total|variable_paths|stability|bitmap_cvg|unique_crashes|unique_hangs)[[:space:]]*:' \
    "${OUTDIR}/fuzzer_stats" || true
fi
# GNU timeout returns 124 after it sends the expected interrupt at duration end.
if [[ ${STATUS} -eq 124 ]]; then exit 0; fi
exit "${STATUS}"
