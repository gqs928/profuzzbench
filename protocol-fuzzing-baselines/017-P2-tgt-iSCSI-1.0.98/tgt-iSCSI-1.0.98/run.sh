#!/usr/bin/env bash
set -Eeuo pipefail

OUTDIR=${1:-/results/iscsi-fuzz}
TIMEOUT=${2:-60s}
SEEDS=${SEEDS:-/workspace/seeds}
DICT=${DICT:-/workspace/iscsi.dict}
mkdir -p "$(dirname "${OUTDIR}")"
[[ -d ${SEEDS} ]] || { echo "iSCSI seeds missing: ${SEEDS}" >&2; exit 2; }
[[ -f ${DICT} ]] || { echo "iSCSI dictionary missing: ${DICT}" >&2; exit 2; }
if [[ -e ${OUTDIR} ]] && [[ -n $(find "${OUTDIR}" -mindepth 1 -maxdepth 1 -print -quit) ]]; then
  echo "Output directory is not empty: ${OUTDIR}" >&2
  exit 2
fi

set +e
timeout --signal=INT --kill-after=10s "${TIMEOUT}" \
  /opt/aflnet/afl-fuzz -d -i "${SEEDS}" -x "${DICT}" -o "${OUTDIR}" \
  -N "tcp://127.0.0.1/${ISCSI_PORT:-3260}" -P ISCSI -E -q 3 -s 3 \
  -R -K -D 100000 -W 100 -w 100000 -m none -t 5000+ \
  /opt/benchmark/tgt-runner
status=$?
set -e
echo "AFLNet exit status: ${status}"
if [[ -f ${OUTDIR}/fuzzer_stats ]]; then
  grep -E '^(execs_done|paths_total|variable_paths|stability|bitmap_cvg|unique_crashes|unique_hangs)[[:space:]]*:' \
    "${OUTDIR}/fuzzer_stats" || true
fi
if [[ ${status} -eq 124 ]]; then exit 0; fi
exit "${status}"
