#!/usr/bin/env bash
set -euo pipefail

out=${1:-/work/results/validation}
mkdir -p "$out"

/src/opensips/opensips -F -f /work/opensips.cfg -s F_PARALLEL_MALLOC >"$out/opensips.log" 2>&1 &
server_pid=$!
cleanup() {
  kill -TERM "$server_pid" 2>/dev/null || true
  for _ in $(seq 1 50); do
    kill -0 "$server_pid" 2>/dev/null || break
    sleep 0.1
  done
  kill -KILL "$server_pid" 2>/dev/null || true
  wait "$server_pid" 2>/dev/null || true
}
trap cleanup EXIT

python3 - "$out/service-smoke.json" <<'PY'
import json, socket, sys, time
out = sys.argv[1]
packet = (
    b"OPTIONS sip:service@example.test SIP/2.0\r\n"
    b"Via: SIP/2.0/UDP 127.0.0.1:5062;branch=z9hG4bKsmoke;rport\r\n"
    b"Max-Forwards: 70\r\n"
    b"From: <sip:fuzzer@example.test>;tag=smoke\r\n"
    b"To: <sip:service@example.test>\r\n"
    b"Call-ID: smoke@benchmark.example\r\n"
    b"CSeq: 1 OPTIONS\r\nContent-Length: 0\r\n\r\n"
)
response = None
for _ in range(100):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(0.25)
            sock.sendto(packet, ("127.0.0.1", 5060))
            response, _ = sock.recvfrom(8192)
        break
    except OSError:
        time.sleep(0.1)
if response is None or not response.startswith(b"SIP/2.0 200"):
    raise SystemExit(f"OpenSIPS did not return a valid SIP 200 response: {response!r}")
if not response.endswith(b"\r\n\r\n"):
    raise SystemExit("SIP response terminator missing")
open(out, "w").write(json.dumps({"protocol":"SIP/UDP","opensips_version":"4.0.3","response_status":200,"response_bytes":len(response),"pass":True}, indent=2)+"\n")
PY

grep -Fq '4.0.3' <(/src/opensips/opensips -V 2>&1)
kill -0 "$server_pid"
