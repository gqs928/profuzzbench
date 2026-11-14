#!/usr/bin/env bash
set -euo pipefail

if (( EUID != 0 )); then
  echo "Run Courier as container root so its login helper can switch to the mailbox user." >&2
  exit 2
fi

PROFILE=${1:-pop3}
OUTDIR=${2:-/results/${PROFILE}-smoke}
TIMEOUT=${3:-60s}
OPTIONS=${4:-}
PREFIX=${COURIER_AFL_PREFIX:-/opt/courier-afl}
AFLNET=${AFLNET:-/opt/aflnet}
FUZZER=${FUZZER_BIN:-${AFLNET}/afl-fuzz}

case "${PROFILE}" in
  pop3)
    PROTOCOL=POP3
    PORT=1110
    SEEDS=/opt/benchmark/seeds/pop3
    DICT=/workspace/pop3.dict
    ;;
  imap)
    PROTOCOL=IMAP
    PORT=1143
    SEEDS=/opt/benchmark/seeds/imap
    DICT=/workspace/imap.dict
    ;;
  *) echo "profile must be pop3 or imap" >&2; exit 2 ;;
esac

TARGET=/opt/benchmark/courier-runner
for path in "${FUZZER}" "${TARGET}" "${DICT}"; do
  [[ -x ${path} || -f ${path} ]] || { echo "missing target input: ${path}" >&2; exit 2; }
done
[[ -d ${SEEDS} ]] || { echo "missing seed directory: ${SEEDS}" >&2; exit 2; }
[[ -x /workspace/reset-maildir.sh ]] || { echo "missing mailbox reset hook" >&2; exit 2; }
[[ -n $(find "${SEEDS}" -maxdepth 1 -type f -print -quit) ]] || { echo "no seed files in ${SEEDS}" >&2; exit 2; }

mkdir -p "$(dirname "${OUTDIR}")"
if [[ -e ${OUTDIR} ]] && [[ -n $(find "${OUTDIR}" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null) ]]; then
  echo "result directory is not empty: ${OUTDIR}" >&2
  exit 2
fi
mkdir -p "${OUTDIR}"
export PATH="${PREFIX}/bin:${PREFIX}/sbin:${PREFIX}/libexec:/usr/local/bin:/usr/local/sbin:${PATH}"
export LD_LIBRARY_PATH="${PREFIX}/lib:/usr/local/lib${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"
export COURIER_AFL_PREFIX=${PREFIX}
/workspace/reset-maildir.sh
/usr/local/sbin/authdaemond start
cleanup() {
  pkill -TERM -x couriertcpd 2>/dev/null || true
  pkill -TERM -x pop3d 2>/dev/null || true
  pkill -TERM -x imapd 2>/dev/null || true
  /usr/local/sbin/authdaemond stop >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM
AUTH_SOCKET=/usr/local/var/spool/authdaemon/socket
for _ in {1..100}; do
  [[ -S ${AUTH_SOCKET} ]] && break
  sleep 0.05
done
if [[ ! -S ${AUTH_SOCKET} ]]; then
  find /usr/local/var/spool/authdaemon -maxdepth 2 -type s -print >&2 || true
  echo "Courier authdaemon socket did not appear" >&2
  exit 2
fi

read -r -a EXTRA_OPTIONS <<< "${OPTIONS}"
{
  printf 'protocol=%s\nport=%s\n' "${PROTOCOL}" "${PORT}"
  printf 'profile=%s\nserver_prefix=%s\n' "${PROFILE}" "${PREFIX}"
  printf 'duration_requested=%s\nseed_count=%s\n' "${TIMEOUT}" "$(find "${SEEDS}" -maxdepth 1 -type f | wc -l)"
  printf 'fuzzer=%s\n' "${FUZZER}"
} > "${OUTDIR}/run-parameters.txt"

set +e
timeout --signal=INT --kill-after=15s "${TIMEOUT}" "${FUZZER}" -d -i "${SEEDS}" -x "${DICT}" -o "${OUTDIR}" -N "tcp://127.0.0.1/${PORT}" -P "${PROTOCOL}" -E -q 3 -s 3 -R -K -D 100000 -W 100 -w 100000 -m none -t 10000+ -c /workspace/reset-maildir.sh "${EXTRA_OPTIONS[@]}" "${TARGET}" "${PROFILE}" 2>&1 | tee "${OUTDIR}/fuzz.log"
STATUS=${PIPESTATUS[0]}
set -e
printf 'fuzzer_exit_status=%s\n' "${STATUS}" >> "${OUTDIR}/run-parameters.txt"
if [[ -f ${OUTDIR}/fuzzer_stats ]]; then
  grep -E '^(run_time|execs_done|paths_total|variable_paths|stability|bitmap_cvg|unique_crashes|unique_hangs)[[:space:]]*:' "${OUTDIR}/fuzzer_stats" || true
fi
chmod -R a+rX "${OUTDIR}"
if [[ ${STATUS} -eq 124 || ${STATUS} -eq 0 ]]; then exit 0; fi
exit "${STATUS}"
