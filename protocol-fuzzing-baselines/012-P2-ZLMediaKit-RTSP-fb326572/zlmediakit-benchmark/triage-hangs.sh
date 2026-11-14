#!/usr/bin/env bash
set -euo pipefail

OUTDIR="${1:?usage: triage-hangs.sh RESULTS_DIR}"
INPUT_DIR="$OUTDIR/aflnet-out/replayable-hangs"
TRIAGE_DIR="$OUTDIR/hang-triage"
mkdir -p "$TRIAGE_DIR"

gcc -O2 -o /tmp/aflnet-replay /opt/aflnet/aflnet-replay.c /opt/aflnet/aflnet.c

health_check() {
  python3 - <<'PY'
import socket, time
for _ in range(40):
    try:
        with socket.create_connection(('127.0.0.1', 8554), timeout=1) as sock:
            sock.settimeout(2)
            sock.sendall(b'OPTIONS rtsp://127.0.0.1/live/test RTSP/1.0\r\nCSeq: 90\r\n\r\n')
            data = bytearray()
            while b'\r\n\r\n' not in data and len(data) < 65536:
                part = sock.recv(4096)
                if not part:
                    break
                data.extend(part)
            if data.startswith(b'RTSP/1.0 200'):
                print('OPTIONS=200')
                raise SystemExit(0)
    except OSError:
        time.sleep(0.25)
print('OPTIONS=FAIL')
raise SystemExit(1)
PY
}

for testcase in "$INPUT_DIR"/*; do
  [[ -f "$testcase" ]] || continue
  name="$(basename "$testcase")"
  server_log="$TRIAGE_DIR/$name.server.log"
  replay_log="$TRIAGE_DIR/$name.replay.log"
  result_file="$TRIAGE_DIR/$name.result.txt"
  /opt/zlmediakit/MediaServer -c /work/config.ini -l 2 -t 2 >"$server_log" 2>&1 &
  server_pid=$!
  if ! health_check >/dev/null 2>&1; then
    printf 'candidate=%s\npre_health=FAIL\n' "$name" > "$result_file"
    kill -TERM "$server_pid" 2>/dev/null || true
    wait "$server_pid" 2>/dev/null || true
    continue
  fi

  set +e
  timeout 90 /tmp/aflnet-replay "$testcase" RTSP 8554 1000 1000000 >"$replay_log" 2>&1
  replay_rc=$?
  set -e

  set +e
  post_health="$(health_check 2>&1)"
  health_rc=$?
  set -e
  if kill -0 "$server_pid" 2>/dev/null; then server_process=alive; else server_process=exited; fi
  {
    printf 'candidate=%s\nreplay_exit_code=%s\nserver_process=%s\npost_health_exit_code=%s\npost_health=%s\n' \
      "$name" "$replay_rc" "$server_process" "$health_rc" "$post_health"
  } > "$result_file"
  kill -TERM "$server_pid" 2>/dev/null || true
  wait "$server_pid" 2>/dev/null || true
done

chmod -R a+rX "$TRIAGE_DIR"
cat "$TRIAGE_DIR"/*.result.txt
