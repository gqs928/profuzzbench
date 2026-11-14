#!/usr/bin/env bash
set -euo pipefail

CANDIDATE_DIR="${1:-/work/results/rtsp-30m/aflnet-out/replayable-hangs}"
OUTROOT="${2:-/work/results/rtsp-30m/candidate-replay}"
REPLAY_TIMEOUT="${REPLAY_TIMEOUT:-6}"
SEQ="$(find "${CANDIDATE_DIR}" -maxdepth 1 -type f -print | sort | head -1)"
[[ -n "${SEQ}" ]] || { echo "No AFLNet timeout candidate found in ${CANDIDATE_DIR}." >&2; exit 2; }
if [[ -e "${OUTROOT}" ]] && [[ -n "$(find "${OUTROOT}" -mindepth 1 -maxdepth 1 -print -quit)" ]]; then
  echo "Replay output is nonempty: ${OUTROOT}. Choose a fresh path." >&2
  exit 2
fi

mkdir -p "${OUTROOT}"
sha256sum "${SEQ}" > "${OUTROOT}/candidate.sha256"
printf 'candidate=%s\nrepeats=3\ntimeout_seconds=%s\nservice_reset=one fresh MediaMTX process per replay\n' \
  "$(basename "${SEQ}")" "${REPLAY_TIMEOUT}" > "${OUTROOT}/replay-method.txt"

for trial in 1 2 3; do
  DIR="${OUTROOT}/trial-${trial}"
  mkdir -p "${DIR}/go-coverdata" "${DIR}/server-work"
  (
    cd "${DIR}/server-work"
    GOCOVERDIR="${DIR}/go-coverdata" exec /opt/mediamtx/mediamtx /work/mediamtx.yml
  ) > "${DIR}/server.log" 2>&1 &
  SERVER_PID=$!

  if ! python3 - <<'PY'
import socket, sys, time
deadline=time.monotonic()+30
last='not ready'
while time.monotonic()<deadline:
    try:
        with socket.create_connection(("127.0.0.1",8554),timeout=1) as s:
            s.sendall(b"OPTIONS rtsp://127.0.0.1:8554/ready RTSP/1.0\r\nCSeq: 1\r\n\r\n")
            if s.recv(4096).startswith(b"RTSP/1.0 200"):
                sys.exit(0)
            last='OPTIONS did not return 200'
    except OSError as e:
        last=repr(e)
    time.sleep(.1)
print(f"MediaMTX readiness failed: {last}",file=sys.stderr)
sys.exit(1)
PY
  then
    kill -TERM "${SERVER_PID}" >/dev/null 2>&1 || true
    wait "${SERVER_PID}" >/dev/null 2>&1 || true
    echo "MediaMTX replay trial ${trial} did not become ready." >&2
    exit 1
  fi

  set +e
  python3 /work/replay_rtsp_sequence.py "${SEQ}" --timeout "${REPLAY_TIMEOUT}" --delay-ms 500 \
    --output "${DIR}/replay.json" > "${DIR}/replay.stdout.txt" 2> "${DIR}/replay.stderr.txt"
  REPLAY_STATUS=$?
  set -e

  set +e
  python3 - <<'PY' > "${DIR}/post-replay-health.txt" 2>&1
import socket, sys
with socket.create_connection(("127.0.0.1",8554),timeout=3) as s:
    s.sendall(b"OPTIONS rtsp://127.0.0.1:8554/health RTSP/1.0\r\nCSeq: 1\r\n\r\n")
    response=s.recv(4096).decode("latin1","replace")
    print(response.split("\r\n",1)[0])
    sys.exit(0 if response.startswith("RTSP/1.0 200") else 1)
PY
  HEALTH_STATUS=$?
  set -e

  kill -TERM "${SERVER_PID}" >/dev/null 2>&1 || true
  for _ in $(seq 1 300); do
    state='gone'
    if [[ -r "/proc/${SERVER_PID}/status" ]]; then state="$(awk '/^State:/ {print $2}' "/proc/${SERVER_PID}/status")"; fi
    [[ "${state}" == gone || "${state}" == Z || "${state}" == X ]] && break
    sleep .1
  done
  state='gone'
  if [[ -r "/proc/${SERVER_PID}/status" ]]; then state="$(awk '/^State:/ {print $2}' "/proc/${SERVER_PID}/status")"; fi
  FORCED=no
  if [[ "${state}" != gone && "${state}" != Z && "${state}" != X ]]; then
    FORCED=yes
    kill -KILL "${SERVER_PID}" >/dev/null 2>&1 || true
  fi
  set +e
  wait "${SERVER_PID}"
  SERVER_STATUS=$?
  set -e
  COUNTERS=no
  if test -n "$(find "${DIR}/go-coverdata" -type f -name 'covcounters.*' -print -quit)"; then COUNTERS=yes; fi
  printf 'replay_exit_code=%s\npost_replay_health_exit_code=%s\nserver_graceful=%s\nserver_exit_code=%s\n' \
    "${REPLAY_STATUS}" "${HEALTH_STATUS}" \
    "$( [[ "${FORCED}" == no && "${SERVER_STATUS}" -eq 0 ]] && echo yes || echo no )" \
    "${SERVER_STATUS}" > "${DIR}/trial-status.txt"
  printf 'go_coverage_counters_flushed=%s\n' "${COUNTERS}" >> "${DIR}/trial-status.txt"
done

printf 'result=inspect each replay.json; do not treat a single timeout as a confirmed defect\n' \
  > "${OUTROOT}/classification.txt"
