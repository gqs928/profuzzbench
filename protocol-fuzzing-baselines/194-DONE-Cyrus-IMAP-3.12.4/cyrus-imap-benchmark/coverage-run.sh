#!/usr/bin/env bash
set -euo pipefail

if (($# < 2)); then
  echo "usage: coverage-run.sh FUZZ_OUTPUT_DIR OUTPUT_DIR [QUEUE_LIMIT]" >&2
  exit 2
fi
FUZZ_DIR=$1
OUTDIR=$2
LIMIT=${3:-200}
TARGET_ROOT=/home/ubuntu/experiments/cyrus-gcov

if [[ -e ${OUTDIR} ]] && [[ -n $(find "${OUTDIR}" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null) ]]; then
  echo "Output directory is nonempty: ${OUTDIR}. Choose a fresh path." >&2
  exit 2
fi
mkdir -p "${OUTDIR}"
find "${TARGET_ROOT}" -type f -name '*.gcda' -delete
CYRUS_GCOV_PREFIX="${TARGET_ROOT}" python3 /workspace/coverage_replay.py "${FUZZ_DIR}" "${OUTDIR}/replay" "${LIMIT}"
GCDA_COUNT=$(find "${TARGET_ROOT}" -type f -name '*.gcda' | wc -l)
if [[ ${GCDA_COUNT} -lt 1 ]]; then
  echo "No gcov data was written under ${TARGET_ROOT}; refusing to publish a coverage report." >&2
  exit 1
fi
if [[ ! -s "${TARGET_ROOT}/imap/imapd.gcda" ]]; then
  echo "No imapd.gcda was flushed; the IMAP command handlers were not measured." >&2
  exit 1
fi
{
  printf 'server_build=%s\n' "${TARGET_ROOT}"
  printf 'instrumentation=GCC gcov (--coverage)\n'
  printf 'gcda_file_count=%s\n' "${GCDA_COUNT}"
  printf 'imapd_gcda_bytes=%s\n' "$(stat -c %s "${TARGET_ROOT}/imap/imapd.gcda")"
  find "${TARGET_ROOT}" -type f -name '*.gcda' -printf '%P %s bytes\n' | sort
} > "${OUTDIR}/coverage-provenance.txt"

mkdir -p "${OUTDIR}/coverage"
(
  cd "${TARGET_ROOT}"
  gcovr --root "${TARGET_ROOT}" --object-directory "${TARGET_ROOT}" --html-details "${OUTDIR}/coverage/index.html" .
  gcovr --root "${TARGET_ROOT}" --object-directory "${TARGET_ROOT}" --print-summary . > "${OUTDIR}/coverage-summary.txt"
  gcovr --root "${TARGET_ROOT}" --object-directory "${TARGET_ROOT}" --json-pretty . > "${OUTDIR}/coverage/gcovr.json"
)
(
  cd "${OUTDIR}"
  find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS
)
echo "Coverage report: ${OUTDIR}/coverage/index.html; summary=${OUTDIR}/coverage-summary.txt"
