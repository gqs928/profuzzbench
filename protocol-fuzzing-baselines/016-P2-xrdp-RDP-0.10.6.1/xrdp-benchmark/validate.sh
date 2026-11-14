#!/usr/bin/env bash
set -euo pipefail
OUTDIR="${1:?usage: validate.sh RESULTS_DIR}"
test -s "$OUTDIR/build-lock.txt"
test -s "$OUTDIR/config-check.txt"
test -s "$OUTDIR/aflnet.log"
test -s "$OUTDIR/aflnet-out/fuzzer_stats"
test -s "$OUTDIR/aflnet-out/ipsm.dot"
test -s "$OUTDIR/preflight/rdp-smoke.json"
test -s "$OUTDIR/post-smoke/rdp-smoke.json"
grep -q '"status": "pass"' "$OUTDIR/preflight/rdp-smoke.json"
grep -q '"status": "pass"' "$OUTDIR/post-smoke/rdp-smoke.json"
python3 - "$OUTDIR" <<'PY'
import json,pathlib,sys
p=pathlib.Path(sys.argv[1])
elapsed=int((p/'fuzz-end-epoch.txt').read_text())-int((p/'external-start-epoch.txt').read_text())
stats={}
for line in (p/'aflnet-out/fuzzer_stats').read_text().splitlines():
    if ':' in line:
        k,v=line.split(':',1); stats[k.strip()]=v.strip()
assert elapsed >= 20, f'campaign ended too early: {elapsed}s'
assert int(stats.get('execs_done','0')) > 0, 'AFLNet completed no executions'
assert int(stats.get('unique_crashes','0')) == 0, 'campaign produced a crash requiring triage'
assert (p/'aflnet-out/ipsm.dot').stat().st_size > 32, 'RDP response-state graph is empty'
pre=json.loads((p/'preflight/rdp-smoke.json').read_text())
post=json.loads((p/'post-smoke/rdp-smoke.json').read_text())
print(f'ACCEPTANCE_PASS elapsed_seconds={elapsed} executions={stats.get("execs_done")} bitmap_cvg={stats.get("bitmap_cvg")} states_graph_bytes={(p/"aflnet-out/ipsm.dot").stat().st_size} selected_protocol={pre["selected_protocol"]} post_smoke={post["status"]}')
PY
