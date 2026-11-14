#!/usr/bin/env bash
set -euo pipefail

# Acceptance-only controlled fault test. The production Memcached source and
# image are unchanged; the preload hook exists only in this disposable run.
OUT=${1:-/results/crash-injection}
WORKDIR=${WORKDIR:-/home/ubuntu/experiments}
AFLNET=${AFLNET:-/home/ubuntu/aflnet}
PORT=${PORT:-11213}
PACKAGE_DIR=${PACKAGE_DIR:-/workspace}
TARGET=${WORKDIR}/memcached-fuzz/memcached
HOOK=/tmp/libmemcached-fault-injection.so
INPUT=/tmp/memcached-fault-seed
mkdir -p "${OUT}"

cc -shared -fPIC -O2 -Wall -Wextra "${PACKAGE_DIR}/fault_injection.c" -ldl -o "${HOOK}"
mkdir -p "${INPUT}"
printf 'BRASHNOW\r\n' > "${INPUT}/seed-controlled-crash"
if [[ -e ${OUT}/crashes ]] && [[ -n $(find "${OUT}/crashes" "${OUT}/replayable-crashes" -mindepth 1 -maxdepth 1 -print -quit) ]]; then
  echo "Output already contains crash artifacts: ${OUT}" >&2
  exit 2
fi

export ASAN_OPTIONS=abort_on_error=1:symbolize=0:detect_leaks=0:detect_stack_use_after_return=1
export AFL_PRELOAD=${HOOK}
set +e
timeout --signal=INT --kill-after=5s 120s "${AFLNET}/afl-fuzz" -i "${INPUT}" -o "${OUT}" -N "tcp://127.0.0.1/${PORT}" -P MEMCACHED -E -q 3 -s 3 -R -K -D 10000 -W 100 -w 100000 -m none -t 5000+ "${TARGET}" -B ascii -p "${PORT}" -U 0 -t 1 >"${OUT}/fuzzer.log" 2>&1
FUZZ_STATUS=$?
set -e
unset AFL_PRELOAD

CRASH=$(find "${OUT}/replayable-crashes" -maxdepth 1 -type f -name 'id:*' -print -quit 2>/dev/null || true)
if [[ -z ${CRASH} ]]; then
  echo "FAIL: AFLNet did not record the controlled server abort (fuzzer exit=${FUZZ_STATUS}); see ${OUT}/fuzzer.log" >&2
  exit 1
fi
cp "${CRASH}" "${OUT}/controlled-crash.aflnet"
tail -c +5 "${CRASH}" > "${OUT}/controlled-crash.sample"
set +e
SERVER_PRELOAD=${HOOK} LOG="${OUT}/replay.log" PORT=${PORT} bash "${PACKAGE_DIR}/crash_script.sh" "${OUT}/controlled-crash.sample" >>"${OUT}/replay.log" 2>&1
REPLAY_STATUS=$?
set -e
if [[ ${REPLAY_STATUS} -eq 0 ]]; then
  echo 'FAIL: the controlled crash sample did not reproduce an abnormal server exit.' >&2
  exit 1
fi
if ! grep -Eq 'Server exited during replay|Aborted|SIGABRT|status 134' "${OUT}/replay.log"; then
  echo 'FAIL: replay did not show a process-level abnormal exit.' >&2
  exit 1
fi
{
  echo 'PASS: test-only preload caused a controlled Memcached process abort.'
  echo 'PASS: AFLNet saved the triggering input under crashes/.'
  echo "PASS: replayed sample exited abnormally (status ${REPLAY_STATUS})."
  echo 'The preload library and seed were created in /tmp inside the disposable container; production files were not patched.'
} > "${OUT}/summary.txt"
cat "${OUT}/summary.txt"
