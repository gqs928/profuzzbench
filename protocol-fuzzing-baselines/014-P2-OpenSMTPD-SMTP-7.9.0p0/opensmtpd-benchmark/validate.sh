#!/usr/bin/env bash
set -euo pipefail
OUTDIR="${1:?usage: validate.sh RESULTS_DIR}"
test -s "$OUTDIR/build-lock.txt"
test -s "$OUTDIR/config-check.txt"
test -s "$OUTDIR/aflnet.log"
test -s "$OUTDIR/aflnet-out/fuzzer_stats"
test -s "$OUTDIR/campaign/gcov-summary.json"
test -s "$OUTDIR/campaign/gcov-summary.txt"
test -s "$OUTDIR/preflight/smtp-smoke.json"
test -s "$OUTDIR/post-smoke/smtp-smoke.json"
grep -q '"status": "pass"' "$OUTDIR/preflight/smtp-smoke.json"
grep -q '"status": "pass"' "$OUTDIR/post-smoke/smtp-smoke.json"
test "$(sed -n 's/^target_version=//p' "$OUTDIR/build-lock.txt")" = 7.9.0p0
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
coverage=json.loads((p/'campaign/gcov-summary.json').read_text())
assert coverage.get('line_covered',0) > 0, 'no OpenSMTPD source lines were covered'
assert int((p/'campaign/coverage-files.txt').read_text().split('=')[1]) > 0, 'campaign GCOV counters were not flushed'
print(f'ACCEPTANCE_PASS elapsed_seconds={elapsed} executions={stats.get("execs_done")} afl_helper_bitmap={stats.get("bitmap_cvg")} OpenSMTPD_lines={coverage["line_covered"]}/{coverage["line_total"]}')
PY
