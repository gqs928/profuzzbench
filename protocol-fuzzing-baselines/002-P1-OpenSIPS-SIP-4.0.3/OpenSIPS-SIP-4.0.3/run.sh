#!/usr/bin/env bash
set -euo pipefail

out=${1:-/work/results/sip-30m}
duration=${2:-1800}
inputs=${INPUT_DIR:-/work/seeds}
mkdir -p "$out"
if [[ -e "$out/aflnet-out" ]]; then
  echo "AFLNet output already exists: $out/aflnet-out. Choose a fresh output directory." >&2
  exit 2
fi

set +e
timeout --signal=INT --kill-after=10s "${duration}s" \
  /opt/aflnet/afl-fuzz -d -i "$inputs" -o "$out/aflnet-out" \
  -N udp://127.0.0.1/5060 -P SIP -D 1000000 -W 100 -w 100000 \
  -E -F -R -K -q 3 -s 3 -t 5000+ -m none \
  -T "OpenSIPS 4.0.3 SIP/UDP" -- \
  /src/opensips/opensips -F -f /work/opensips.cfg -s F_PARALLEL_MALLOC \
  >"$out/aflnet.log" 2>&1
fuzzer_rc=$?
set -e

stats="$out/aflnet-out/fuzzer_stats"
test -s "$stats"
cp "$stats" "$out/fuzzer_stats"
grep -E '^(start_time|last_update|cycles_done|execs_done|execs_per_sec|paths_total|paths_favored|paths_found|paths_imported|unique_crashes|unique_hangs|stability|bitmap_cvg|afl_banner|command_line)' "$stats" > "$out/fuzzer-summary.txt"
python3 - "$out/run.json" "$duration" "$fuzzer_rc" "$stats" <<'PY'
import json, sys
from pathlib import Path
out, duration, rc, stats = sys.argv[1:]
fields = {}
for line in Path(stats).read_text(errors="replace").splitlines():
    if ":" in line:
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip()
observed = int(fields.get("last_update", "0")) - int(fields.get("start_time", "0"))
if observed < int(duration) - 5:
    raise SystemExit(f"AFLNet statistics show {observed}s for a requested {duration}s campaign")
json.dump({"protocol":"SIP/UDP","duration_seconds":int(duration),"observed_runtime_seconds":observed,"aflnet_exit_code":int(rc),"fuzzer_stats":fields}, open(out,"w"), indent=2)
PY
