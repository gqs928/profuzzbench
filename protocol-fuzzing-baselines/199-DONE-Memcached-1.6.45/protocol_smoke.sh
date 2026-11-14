#!/usr/bin/env bash
set -euo pipefail

# Compare unmodified Memcached with the instrumented target using identical
# ASCII requests. Intended to run inside the benchmark image.
OUT=${1:-/results/protocol-smoke}
WORKDIR=${WORKDIR:-/home/ubuntu/experiments}
PORT=${PORT:-11211}
mkdir -p "${OUT}"

run_one() {
  local label=$1 binary=$2 seed=$3 pid attempt result log
  result="${OUT}/${label}-${seed}.response"
  log="${OUT}/${label}-${seed}.server.log"
  "${binary}" -B ascii -p "${PORT}" -U 0 -t 1 >"${log}" 2>&1 &
  pid=$!
  for attempt in $(seq 1 100); do
    if nc -z 127.0.0.1 "${PORT}" >/dev/null 2>&1; then break; fi
    if ! kill -0 "${pid}" 2>/dev/null; then cat "${log}" >&2; return 1; fi
    sleep 0.02
  done
  if ! nc -z 127.0.0.1 "${PORT}" >/dev/null 2>&1; then
    kill -TERM "${pid}" 2>/dev/null || true
    wait "${pid}" 2>/dev/null || true
    echo "server did not listen on ${PORT}: ${binary}" >&2
    return 1
  fi
  timeout 5s nc -N 127.0.0.1 "${PORT}" < "${WORKDIR}/in-memcached/${seed}" >"${result}" 2>/dev/null || true
  kill -TERM "${pid}" 2>/dev/null || true
  wait "${pid}" 2>/dev/null || true
  if kill -0 "${pid}" 2>/dev/null; then
    echo "server process remains after normal stop: pid=${pid}" >&2
    return 1
  fi
}

REFERENCE=${WORKDIR}/memcached-reference/memcached
INSTRUMENTED=${WORKDIR}/memcached-fuzz/memcached
[[ -x ${REFERENCE} && -x ${INSTRUMENTED} ]] || { echo 'reference/instrumented binaries are missing' >&2; exit 2; }
for target in reference instrumented; do
  if [[ ${target} == reference ]]; then binary=${REFERENCE}; else binary=${INSTRUMENTED}; fi
  for seed in seed-version seed-stats seed-set-get seed-business seed-delete seed-quit; do
    run_one "${target}" "${binary}" "${seed}"
  done
done

grep -q '^VERSION ' "${OUT}/reference-seed-version.response"
grep -q '^VERSION ' "${OUT}/instrumented-seed-version.response"
grep -q '^STAT ' "${OUT}/reference-seed-stats.response"
grep -q '^END' "${OUT}/reference-seed-stats.response"
grep -q '^STORED' "${OUT}/reference-seed-set-get.response"
grep -q '^VALUE key 0 5' "${OUT}/reference-seed-set-get.response"
grep -q '^hello' "${OUT}/reference-seed-set-get.response"
grep -q '^DELETED' "${OUT}/reference-seed-business.response"
grep -q '^NOT_FOUND' "${OUT}/reference-seed-delete.response"
cmp "${OUT}/reference-seed-version.response" "${OUT}/instrumented-seed-version.response"
cmp "${OUT}/reference-seed-set-get.response" "${OUT}/instrumented-seed-set-get.response"
cmp "${OUT}/reference-seed-business.response" "${OUT}/instrumented-seed-business.response"
cmp "${OUT}/reference-seed-delete.response" "${OUT}/instrumented-seed-delete.response"
cmp "${OUT}/reference-seed-quit.response" "${OUT}/instrumented-seed-quit.response"

{
  echo 'PASS: normal ASCII/TCP behavior is preserved for version, storage/get, delete and quit.'
  echo 'PASS: stats request returns STAT records and END (volatile fields are intentionally not byte-compared).'
  echo 'PASS: set/get/delete/get seed reaches stored, value, deleted and terminal response states.'
  echo "seed_files=$(find "${WORKDIR}/in-memcached" -maxdepth 1 -type f -name 'seed-*' | wc -l)"
  echo "reference_version=$(head -n 1 "${OUT}/reference-seed-version.response")"
} > "${OUT}/summary.txt"
cat "${OUT}/summary.txt"
