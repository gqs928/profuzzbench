#!/usr/bin/env bash
set -euo pipefail
BGPD_BIN=${BGPD_BIN:-/usr/lib/frr/bgpd}
BGP_CONF=${BGP_CONF:-/opt/benchmark/bgpd.conf}
BGP_HOST=${BGP_HOST:-127.0.0.1}
BGP_PORT=${BGP_PORT:-179}
BGPD_PID_FILE=${BGPD_PID_FILE:-/tmp/frr-benchmark-bgpd.pid}
BGPD_LOG_FILE=${BGPD_LOG_FILE:-/results/bgpd.log}
BGPD_VTY_DIR=${BGPD_VTY_DIR:-/tmp/frr-benchmark-bgpd.vty}
EXPECTED=${FRR_EXPECTED_VERSION:-10.7.1}
mkdir -p "$(dirname "$BGPD_PID_FILE")" "$(dirname "$BGPD_LOG_FILE")" "$BGPD_VTY_DIR"
if [[ -f "$BGPD_PID_FILE" ]] && kill -0 "$(cat "$BGPD_PID_FILE")" 2>/dev/null; then
  /bin/bash /opt/benchmark/stop-bgpd.sh
fi
# Do not use `head` here: with `set -o pipefail`, bgpd may receive SIGPIPE
# after emitting the remaining version lines and abort the startup wrapper.
version=$("$BGPD_BIN" --version 2>&1 | sed -n '1p')
grep -Fq "$EXPECTED" <<< "$version" || {
  echo "FRR version mismatch: expected $EXPECTED, got $version" >&2
  exit 2
}
: > "$BGPD_LOG_FILE"
"$BGPD_BIN" -f "$BGP_CONF" -n -Z -S -p "$BGP_PORT" -l "$BGP_HOST" \
  --vty_socket "$BGPD_VTY_DIR" --log stdout --log-level info \
  >>"$BGPD_LOG_FILE" 2>&1 &
pid=$!
echo "$pid" > "$BGPD_PID_FILE"
ready=no
for _ in $(seq 1 100); do
  if ! kill -0 "$pid" 2>/dev/null; then
    tail -80 "$BGPD_LOG_FILE" >&2 || true
    echo "bgpd exited before BGP listener readiness" >&2
    exit 1
  fi
  if python3 - "$BGP_HOST" "$BGP_PORT" <<'PY' >/dev/null 2>&1
import ipaddress,sys
host=sys.argv[1]; port=int(sys.argv[2])
host_hex=ipaddress.IPv4Address(host).packed[::-1].hex().upper()
port_hex=f"{port:04X}"
for path in ("/proc/net/tcp", "/proc/net/tcp6"):
    try:
        rows=open(path, encoding="ascii").read().splitlines()[1:]
    except OSError:
        continue
    for row in rows:
        fields=row.split()
        if len(fields) < 4 or fields[3] != "0A":
            continue
        address, local_port=fields[1].split(":")
        if local_port == port_hex and (address == host_hex or address == "00000000"):
            raise SystemExit(0)
raise SystemExit(1)
PY
  then
    ready=yes
    break
  fi
  sleep 0.1
done
[[ "$ready" == yes ]] || {
  tail -80 "$BGPD_LOG_FILE" >&2 || true
  echo "BGP listener readiness timeout" >&2
  exit 1
}
echo "bgpd ready: version=$version pid=$pid endpoint=$BGP_HOST:$BGP_PORT"
