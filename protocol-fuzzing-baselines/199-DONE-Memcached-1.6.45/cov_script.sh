#!/usr/bin/env bash
set -u

# Replay AFLNet queue inputs against the gcov build.
# Usage: cov_script.sh FUZZ_RESULT_DIR [SKIPCOUNT]
FUZZ_RESULT_DIR=${1:?Usage: cov_script.sh FUZZ_RESULT_DIR [SKIPCOUNT]}
SKIPCOUNT=${2:-5}
WORKDIR=${WORKDIR:-/home/ubuntu/experiments}
GCOV_DIR=${GCOV_DIR:-${WORKDIR}/memcached-gcov}
OUT_CSV=${OUT_CSV:-${FUZZ_RESULT_DIR}/cov_over_time.csv}
PORT=${PORT:-11212}
SERVER=${SERVER:-${GCOV_DIR}/memcached}

[[ -d ${FUZZ_RESULT_DIR}/queue ]] || { echo "Queue not found: ${FUZZ_RESULT_DIR}/queue" >&2; exit 2; }
[[ -x ${SERVER} ]] || { echo "Coverage binary not found: ${SERVER}" >&2; exit 2; }
[[ ${SKIPCOUNT} =~ ^[1-9][0-9]*$ ]] || { echo "SKIPCOUNT must be a positive integer" >&2; exit 2; }
if [[ $(realpath "${GCOV_DIR}") != /home/ubuntu/experiments/memcached-gcov ]]; then
  echo "Refusing to reset counters outside the isolated gcov build: ${GCOV_DIR}" >&2
  exit 2
fi
# Do not mix stale counters from earlier reports or acceptance attempts.
find "${GCOV_DIR}" -type f -name '*.gcda' -delete
mkdir -p "$(dirname "${OUT_CSV}")" "${FUZZ_RESULT_DIR}/cov_html"
printf 'Time,l_per,l_abs,b_per,b_abs\n' > "${OUT_CSV}"
cd "${GCOV_DIR}" || exit 2

count=0
last_file=
extract_counts() {
  local summary line_cov branch_cov
  summary=$(gcovr -r "${GCOV_DIR}" -s 2>/dev/null) || return 1
  line_cov=$(printf '%s\n' "${summary}" | sed -nE 's/^lines:[[:space:]]*([0-9.]+)%[[:space:]]*\(([0-9]+) out of ([0-9]+)\).*/\1,\2/p' | head -n1)
  branch_cov=$(printf '%s\n' "${summary}" | sed -nE 's/^branches:[[:space:]]*([0-9.]+)%[[:space:]]*\(([0-9]+) out of ([0-9]+)\).*/\1,\2/p' | head -n1)
  [[ -n ${line_cov} ]] || line_cov='0,0'
  [[ -n ${branch_cov} ]] || branch_cov='0,0'
  printf '%s,%s\n' "${line_cov}" "${branch_cov}"
}

replay_one() {
  local testcase=$1 pid attempt timestamp counts
  "${SERVER}" -B ascii -p "${PORT}" -U 0 -t 1 >/dev/null 2>&1 &
  pid=$!
  for attempt in $(seq 1 50); do
    if nc -z 127.0.0.1 "${PORT}" >/dev/null 2>&1; then break; fi
    if ! kill -0 "${pid}" 2>/dev/null; then wait "${pid}" 2>/dev/null || true; return 0; fi
    sleep 0.02
  done
  timeout 3s nc -N 127.0.0.1 "${PORT}" < "${testcase}" >/dev/null 2>&1 || true
  kill -TERM "${pid}" 2>/dev/null || true
  wait "${pid}" 2>/dev/null || true
  count=$((count + 1))
  timestamp=$(stat -c %Y "${testcase}" 2>/dev/null || date +%s)
  last_file=${testcase}
  if (( count % SKIPCOUNT == 0 )); then
    counts=$(extract_counts)
    printf '%s,%s\n' "${timestamp}" "${counts}" >> "${OUT_CSV}"
  fi
}

while IFS= read -r -d '' testcase; do replay_one "${testcase}"; done < <(find "${FUZZ_RESULT_DIR}/queue" -type f -name 'id:*' -print0 | sort -z)
if (( count == 0 )); then echo "No queue cases found." >&2; exit 2; fi
if (( count % SKIPCOUNT != 0 )); then
  timestamp=$(stat -c %Y "${last_file}" 2>/dev/null || date +%s)
  counts=$(extract_counts)
  printf '%s,%s\n' "${timestamp}" "${counts}" >> "${OUT_CSV}"
fi

gcovr -r "${GCOV_DIR}" --html --html-details -o "${FUZZ_RESULT_DIR}/cov_html/index.html"
echo "Replayed ${count} queue cases. CSV: ${OUT_CSV}"
echo "HTML report: ${FUZZ_RESULT_DIR}/cov_html/index.html"
