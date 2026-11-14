#!/usr/bin/env bash
set -u
if (( EUID != 0 )); then
  echo "Run AFLNet as container root so Dovecot can launch its configured user workers" >&2
  exit 2
fi

OUTDIR=${1:-/results/pop3-smoke}
TIMEOUT=${2:-60s}
OPTIONS=${3:-}
WORKDIR=${WORKDIR:-/home/ubuntu/experiments}
AFLNET=${AFLNET:-/home/ubuntu/aflnet}
FUZZER_BIN=${FUZZER_BIN:-${AFLNET}/afl-fuzz}
INPUTS=${INPUTS:-${WORKDIR}/seeds}
DICT=${DICT:-/workspace/pop3.dict}
PREFIX=${DOVECOT_AFL_PREFIX:-${WORKDIR}/dovecot-afl}
PORT=${POP3_PORT:-1110}

[[ -x ${FUZZER_BIN} ]] || { echo "AFLNet missing: ${FUZZER_BIN}" >&2; exit 2; }
[[ -d ${INPUTS} ]] || { echo "POP3 corpus missing: ${INPUTS}" >&2; exit 2; }
[[ -f ${DICT} ]] || { echo "POP3 dictionary missing: ${DICT}" >&2; exit 2; }
[[ -x /workspace/clean.sh ]] || { echo "Mailbox reset hook missing" >&2; exit 2; }
grep -a -q 'POP3' "${FUZZER_BIN}" || { echo "AFLNet lacks POP3 parser" >&2; exit 2; }
if [[ -e ${OUTDIR} ]] && [[ -n $(find "${OUTDIR}" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null) ]]; then
  echo "Result directory is nonempty: ${OUTDIR}" >&2
  exit 2
fi
mkdir -p "$(dirname "${OUTDIR}")" "${OUTDIR}"
read -r -a EXTRA_OPTIONS <<< "${OPTIONS}"
export LD_LIBRARY_PATH="${PREFIX}/lib${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"
export DOVECOT_AFL_PREFIX=${PREFIX}
/usr/local/sbin/dovecot-root-launcher afl reset
runuser -u ubuntu -- python3 /workspace/prepare_maildir.py
START_EPOCH=$(date -u +%s)
{
  printf 'started_utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  printf 'duration_requested=%s\n' "${TIMEOUT}"
  printf 'protocol=POP3\nport=%s\n' "${PORT}"
  printf 'seed_dir=%s\nseed_count=%s\n' "${INPUTS}" "$(find "${INPUTS}" -maxdepth 1 -type f | wc -l)"
  printf 'fuzzer=%s\ntarget=/usr/local/sbin/dovecot-pop3-runner\n' "${FUZZER_BIN}"
  printf 'image_variant=%s\n' "${PREFIX}"
} > "${OUTDIR}/run-parameters.txt"
echo "Running AFLNet POP3 state feedback on isolated loopback TCP/${PORT}; output=${OUTDIR}"
set +e
timeout --signal=INT --kill-after=15s "${TIMEOUT}" "${FUZZER_BIN}" -d \
  -i "${INPUTS}" -x "${DICT}" -o "${OUTDIR}" \
  -N "tcp://127.0.0.1/${PORT}" -P POP3 -E -q 3 -s 3 -R -K \
  -D 500000 -W 100 -w 100000 -m none -t 10000+ \
  -c /usr/local/sbin/dovecot-clean-maildir \
  "${EXTRA_OPTIONS[@]}" /usr/local/sbin/dovecot-pop3-runner \
  2>&1 | tee "${OUTDIR}/fuzz.log"
runner_rc=${PIPESTATUS[0]}
set -e
/usr/local/sbin/dovecot-root-launcher afl stop >/dev/null 2>&1 || true
printf 'fuzzer_exit_status=%s\n' "${runner_rc}" >"${OUTDIR}/run-status.txt"
END_EPOCH=$(date -u +%s)
{
  printf 'ended_utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  printf 'elapsed_seconds=%s\n' "$((END_EPOCH - START_EPOCH))"
  printf 'fuzzer_exit_status=%s\n' "${runner_rc}"
} >> "${OUTDIR}/run-parameters.txt"
if [[ -f ${OUTDIR}/fuzzer_stats ]]; then
  grep -E '^(run_time|execs_done|paths_total|variable_paths|stability|bitmap_cvg|unique_crashes|unique_hangs)[[:space:]]*:' "${OUTDIR}/fuzzer_stats" || true
fi
chmod -R a+rX "${OUTDIR}"
if [[ ${runner_rc} -eq 124 || ${runner_rc} -eq 0 ]]; then exit 0; fi
exit "${runner_rc}"
