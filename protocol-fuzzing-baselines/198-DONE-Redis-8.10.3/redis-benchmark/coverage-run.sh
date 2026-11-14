#!/usr/bin/env bash
set -euo pipefail

if (($# < 2)); then
  echo "usage: coverage-run.sh FUZZ_OUTPUT_DIR OUTPUT_DIR [QUEUE_LIMIT]" >&2
  exit 2
fi
FUZZ_DIR=$1
OUTDIR=$2
LIMIT=${3:-200}
TARGET_ROOT=/home/ubuntu/experiments/redis-gcov

if [[ -e ${OUTDIR} ]] && [[ -n $(find "${OUTDIR}" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null) ]]; then
  echo "Output directory is nonempty: ${OUTDIR}. Choose a fresh path." >&2
  exit 2
fi
mkdir -p "${OUTDIR}"
find "${TARGET_ROOT}" -type f -name '*.gcda' -delete
REDIS_GCOV_BIN="${TARGET_ROOT}/src/redis-server" \
  python3 /workspace/coverage_replay.py "${FUZZ_DIR}" "${OUTDIR}/replay" "${LIMIT}"

mkdir -p "${OUTDIR}/coverage"
(
  cd "${TARGET_ROOT}"
  gcovr --root "${TARGET_ROOT}" \
    --object-directory "${TARGET_ROOT}/src" \
    --html "${OUTDIR}/coverage/index.html" \
    src
  (
    cd "${TARGET_ROOT}/src"
    gcov -f -t -o . acl.c networking.c server.c t_string.c t_hash.c multi.c
  ) > "${OUTDIR}/coverage/core-functions-gcov.txt"
  gcovr --root "${TARGET_ROOT}" \
    --object-directory "${TARGET_ROOT}/src" \
    --print-summary src > "${OUTDIR}/coverage-summary.txt"
)
python3 /workspace/summarize_coverage.py \
  "${OUTDIR}/coverage/core-functions-gcov.txt" "${OUTDIR}/core-functions.csv"
(
  cd "${OUTDIR}"
  find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS
)
echo "Coverage reports: ${OUTDIR}/coverage/index.html and ${OUTDIR}/coverage-summary.txt"
