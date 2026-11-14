#!/usr/bin/env bash
set -euo pipefail

PROFILE=${1:-pop3}
OUTDIR=${2:-/results/${PROFILE}-smoke}
PREFIX=${COURIER_REFERENCE_PREFIX:-/opt/courier-reference}
mkdir -p "${OUTDIR}"
export PATH="${PREFIX}/bin:${PREFIX}/sbin:${PREFIX}/libexec:/usr/local/bin:/usr/local/sbin:${PATH}"
export LD_LIBRARY_PATH="${PREFIX}/lib:/usr/local/lib${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"
/workspace/reset-maildir.sh
/usr/local/sbin/authdaemond start
cleanup() {
  if [[ -n ${server_pid:-} ]]; then kill -TERM -- "-${server_pid}" 2>/dev/null || kill -TERM "${server_pid}" 2>/dev/null || true; fi
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
  echo "Courier authdaemon socket did not appear" >&2
  exit 2
fi

if [[ ${PROFILE} == pop3 ]]; then
  PORT=1110
  setsid "${PREFIX}/libexec/couriertcpd" -address=127.0.0.1 -maxprocs=20 -maxperip=20 -nodnslookup "${PORT}" "${PREFIX}/sbin/pop3login" "${PREFIX}/bin/pop3d" Maildir >"${OUTDIR}/server.log" 2>&1 &
  server_pid=$!
  python3 /workspace/protocol_smoke.py --host 127.0.0.1 --port "${PORT}" --username fuzzuser --password resp-benchmark-pass --save-seeds "${OUTDIR}/evidence"
elif [[ ${PROFILE} == imap ]]; then
  PORT=1143
  if [[ ! -f ${PREFIX}/etc/imapaccess.dat ]]; then
    touch "${PREFIX}/etc/imapaccess"
    (cd "${PREFIX}/etc" && "${PREFIX}/bin/makeimapaccess")
  fi
  setsid "${PREFIX}/libexec/couriertcpd" -address=127.0.0.1 -maxprocs=20 -maxperip=20 -access="${PREFIX}/etc/imapaccess.dat" -nodnslookup "${PORT}" "${PREFIX}/sbin/imaplogin" "${PREFIX}/bin/imapd" Maildir >"${OUTDIR}/server.log" 2>&1 &
  server_pid=$!
  python3 /workspace/imap_protocol_smoke.py --host 127.0.0.1 --port "${PORT}" --username fuzzuser --password resp-benchmark-pass --save "${OUTDIR}/evidence.json"
else
  echo "profile must be pop3 or imap" >&2
  exit 2
fi
chmod -R a+rX "${OUTDIR}"
