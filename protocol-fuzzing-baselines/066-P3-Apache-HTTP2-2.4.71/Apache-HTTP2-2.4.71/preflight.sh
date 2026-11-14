#!/usr/bin/env bash
set -euo pipefail
WORKDIR=${WORKDIR:-/opt/benchmark}
SEED_DIR=${SEED_DIR:-${WORKDIR}/seeds}
OUTDIR=${1:-/results/apache-http2-preflight-60s}
PORT=${HTTPD_PORT:-20240}
if [[ -e "$OUTDIR" ]] && [[ -n $(find "$OUTDIR" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null) ]]; then
  echo "result directory must be empty: $OUTDIR" >&2; exit 2
fi
mkdir -p "$OUTDIR"
cleanup() {
  local status=$?
  /bin/bash "$WORKDIR/stop-target.sh" >/dev/null 2>&1 || true
  chmod -R a+rX "$OUTDIR" 2>/dev/null || true
  return "$status"
}
trap cleanup EXIT
/bin/bash "$WORKDIR/prepare-target.sh"
python3 "$WORKDIR/protocol_smoke.py" --host 127.0.0.1 --port "$PORT" --passes 3 \
  --output "$OUTDIR/preflight-smoke.json"
/bin/bash "$WORKDIR/stop-target.sh"
python3 "$WORKDIR/make_seeds.py" "$SEED_DIR"
set +e
python3 "$WORKDIR/deadline_wrapper.py" 60s "$OUTDIR/fuzzer-deadline.json" \
  /opt/aflnet/afl-fuzz -d -i "$SEED_DIR" -o "$OUTDIR" \
  -N "tcp://127.0.0.1/${PORT}" -P HTTP2 -D 100000 -q 3 -s 3 -E -K -W 30 \
  -m none -t 5000 -- /opt/httpd/bin/httpd -f /opt/benchmark/httpd.conf -DFOREGROUND -X
FUZZ_STATUS=$?
set -e
if [[ "$FUZZ_STATUS" -ne 124 && "$FUZZ_STATUS" -ne 130 ]]; then
  echo "60-second AFLNet preflight did not stop at its deadline (status=${FUZZ_STATUS})" >&2
  exit 1
fi
/bin/bash "$WORKDIR/prepare-target.sh"
python3 "$WORKDIR/protocol_smoke.py" --host 127.0.0.1 --port "$PORT" --passes 3 \
  --output "$OUTDIR/postrun-smoke.json"
/bin/bash "$WORKDIR/stop-target.sh"
python3 "$WORKDIR/verify_listener_closed.py" --port "$PORT" --output "$OUTDIR/listener-closed.json"
python3 - "$OUTDIR/fuzzer_stats" <<'PY'
import sys
from pathlib import Path
stats = {}
for line in Path(sys.argv[1]).read_text().splitlines():
    if ':' in line:
        key, value = line.split(':', 1)
        stats[key.strip()] = value.strip()
for key in ('execs_done', 'paths_total', 'unique_crashes', 'unique_hangs', 'stability', 'bitmap_cvg'):
    if key not in stats:
        raise SystemExit(f'missing fuzzer stat: {key}')
if int(stats['execs_done']) < 1 or int(stats['paths_total']) < 1:
    raise SystemExit(f'preflight made no progress: {stats}')
if int(stats['unique_crashes']) or int(stats['unique_hangs']):
    raise SystemExit(f'preflight found crashes or hangs: {stats}')
if float(stats['bitmap_cvg'].rstrip('%')) <= 0:
    raise SystemExit(f'preflight has no AFL-instrumented feedback: {stats}')
if float(stats['stability'].rstrip('%')) < 80:
    raise SystemExit(f'preflight stability is below 80%: {stats}')
print(f"PASS: HTTP/2 fuzzer preflight; execs={stats['execs_done']}, paths={stats['paths_total']}, stability={stats['stability']}")
PY
