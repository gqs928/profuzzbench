#!/usr/bin/env bash
set -Eeuo pipefail

OUTDIR=/work/results/postfix-smtp-30m-20261113
PROFILE="$OUTDIR/replay-verified-gcov"
REPORT="$OUTDIR/replay-verified"
export MAIL_CONFIG=/etc/postfix
mkdir -p "$REPORT" "$PROFILE"
[[ -z "$(find "$REPORT" -mindepth 1 -maxdepth 1 -print -quit)" ]] || {
  echo "verified replay output directory is not empty: $REPORT" >&2
  exit 2
}

prepare_gcov_prefix() {
  local source_dir relative
  while IFS= read -r -d '' source_dir; do
    relative=${source_dir#/src/postfix}
    mkdir -p "$PROFILE$relative"
  done < <(find /src/postfix -type d -print0)
  chmod -R a+rwX "$PROFILE"
}

server_started=0
cleanup() {
  local status=$?
  trap - EXIT INT TERM
  if (( server_started )); then
    /usr/sbin/postfix stop >> "$REPORT/server.log" 2>&1 || status=1
    for _ in $(seq 1 200); do
      /usr/sbin/postfix status >/dev/null 2>&1 || break
      sleep 0.1
    done
  fi
  if /usr/sbin/postfix status >/dev/null 2>&1; then
    status=1
    /usr/sbin/postfix status >> "$REPORT/server.log" 2>&1 || true
  fi
  if ss -ltn | grep -q '127.0.0.1:2525'; then
    echo 'SMTP listener remained open after verified replay' >&2
    status=1
  fi
  if (( status == 0 )); then
    printf 'shutdown=stopped\npostfix_stop_exit_code=0\n' > "$REPORT/stop-status.txt"
  fi
  chmod -R a+rX "$REPORT" "$PROFILE" 2>/dev/null || true
  exit "$status"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

find /src/postfix -type f -name '*.gcda' -delete
prepare_gcov_prefix
export GCOV_PREFIX="$PROFILE" GCOV_PREFIX_STRIP=2
/usr/sbin/postfix start > "$REPORT/server.log" 2>&1
server_started=1
printf '%s\n' "$(cat /var/spool/postfix/pid/master.pid)" > "$REPORT/server.pid.txt"
ready=0
for _ in $(seq 1 180); do
  if python3 - <<'PY' >/dev/null 2>&1
import socket
with socket.create_connection(("127.0.0.1", 2525), timeout=1) as sock:
    sock.settimeout(1)
    greeting = sock.recv(256)
    if not greeting.startswith(b"220"):
        raise SystemExit(1)
    sock.sendall(b"QUIT\r\n")
PY
  then
    /usr/sbin/postfix status >/dev/null 2>&1 || exit 1
    ready=1
    break
  fi
  sleep 0.25
done
(( ready )) || { echo 'Postfix failed readiness before verified replay' >&2; exit 1; }
printf 'start_utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$REPORT/run-times.txt"
python3 /work/replay.py \
  --aflnet-output "$OUTDIR/aflnet-out" \
  --timeout 1 --output "$REPORT/queue-replay.json"
printf 'end_utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$REPORT/run-times.txt"
/usr/sbin/postfix stop >> "$REPORT/server.log" 2>&1
server_started=0
for _ in $(seq 1 200); do
  /usr/sbin/postfix status >/dev/null 2>&1 || break
  sleep 0.1
done
/usr/sbin/postfix status >/dev/null 2>&1 && { echo 'Postfix remained active after replay' >&2; exit 1; }
if ss -ltn | grep -q '127.0.0.1:2525'; then
  echo 'SMTP listener remained open after verified replay' >&2
  exit 1
fi
printf 'shutdown=stopped\npostfix_stop_exit_code=0\n' > "$REPORT/stop-status.txt"

count=$(find "$PROFILE" -type f -name '*.gcda' | wc -l)
printf 'gcda_files=%s\n' "$count" > "$REPORT/coverage-files.txt"
(( count > 0 )) || { echo 'No gcov counters were flushed for verified replay' >&2; exit 1; }
find /src/postfix -type f -name '*.gcda' -delete
cp -a "$PROFILE/." /src/postfix/
(
  cd /src/postfix
  gcovr --root /src/postfix --object-directory /src/postfix \
    --json-summary-pretty --json-summary "$REPORT/gcov-summary.json" \
    --print-summary
) > "$REPORT/gcov-summary.txt"
mkdir -p "$REPORT/gcda"
while IFS= read -r -d '' file; do
  relative=${file#/src/postfix/}
  mkdir -p "$REPORT/gcda/$(dirname "$relative")"
  cp "$file" "$REPORT/gcda/$relative"
done < <(find /src/postfix -type f -name '*.gcda' -print0)
find /src/postfix -type f -name '*.gcda' -delete
chmod -R a+rX "$REPORT" "$PROFILE"
