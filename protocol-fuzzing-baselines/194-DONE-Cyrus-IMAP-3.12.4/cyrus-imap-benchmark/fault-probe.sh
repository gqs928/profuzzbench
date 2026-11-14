#!/usr/bin/env bash
set -euo pipefail

OUT=${1:-/results/fault-probe}
AFLNET=${AFLNET:-/home/ubuntu/aflnet}
FUZZ_TIME=${FAULT_PROBE_TIME:-25s}
mkdir -p "${OUT}/seeds"
printf 'A01 NOOP\r\n' > "${OUT}/seeds/noop"

AFL_USE_ASAN=1 "${AFLNET}/afl-clang-fast" -O1 -g -fno-omit-frame-pointer /workspace/fault_probe_server.c -o "${OUT}/imap_fault_probe"

FUZZ_CMD=("${AFLNET}/afl-fuzz" -i "${OUT}/seeds" -o "${OUT}/aflnet-run" -N tcp://127.0.0.1/1144 -P IMAP -E -q 3 -s 3 -R -K -D 10000 -W 100 -w 100000 -m none -t 1000+ -c /workspace/clean.sh "${OUT}/imap_fault_probe")
printf '%q ' "${FUZZ_CMD[@]}" > "${OUT}/command.txt"
printf '\n' >> "${OUT}/command.txt"

set +e
timeout --signal=INT --kill-after=8s "${FUZZ_TIME}" "${FUZZ_CMD[@]}" > "${OUT}/aflnet.log" 2>&1
status=$?
set -e
printf 'timeout_exit_status=%s\n' "${status}" > "${OUT}/runner-status.txt"

if [[ ! -s "${OUT}/aflnet-run/fuzzer_stats" ]]; then
  echo "AFLNet did not produce fuzzer_stats; see ${OUT}/aflnet.log" >&2
  exit 1
fi
crashes=$(awk -F: '/^unique_crashes[[:space:]]*:/ {gsub(/[[:space:]]/, "", $2); print $2}' "${OUT}/aflnet-run/fuzzer_stats")
saved=$(find "${OUT}/aflnet-run/replayable-crashes" -maxdepth 1 -type f -name 'id:*' | wc -l)
if [[ ${crashes:-0} -lt 1 || ${saved} -lt 1 ]]; then
  echo "AFLNet did not record the deterministic @-triggered crash; see ${OUT}/aflnet.log" >&2
  exit 1
fi
echo "PASS: AFLNet recorded ${crashes} controlled injected crash(es); test server is an isolated fixture, not a Cyrus patch."
