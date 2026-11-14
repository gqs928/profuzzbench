#!/usr/bin/env bash
set -Eeuo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
OUTDIR=${1:-/results}

ssh_ready() { "$ROOT/netconf-ready-check" --once >/dev/null 2>&1; }
if ssh_ready; then exit 0; fi
mkdir -p "$OUTDIR"
log_recovery() {
  printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" >>"$OUTDIR/server-recoveries.log"
}
log_recovery 'action=restart_start reason=ssh_banner_unavailable'

if ! pgrep -f '^sysrepo-plugind([[:space:]]|$)' >/dev/null; then
  sysrepo-plugind -d >>/tmp/sysrepo-plugind.log 2>&1 &
fi
if ! pgrep -f '^sysrepo-notifd([[:space:]]|$)' >/dev/null; then
  sysrepo-notifd -d >>/tmp/sysrepo-notifd.log 2>&1 &
fi

pkill -f '^netopeer2-server([[:space:]]|$)' 2>/dev/null || true
netopeer2-server -d >>/tmp/netopeer2-server.log 2>&1 &
for _ in $(seq 1 40); do
  if ssh_ready; then
    log_recovery 'action=restart_ready'
    exit 0
  fi
  sleep 0.1
done
log_recovery 'action=restart_failed'
exit 1
