#!/usr/bin/env bash
set -euo pipefail
OUTDIR="${1:?usage: validate.sh RESULTS_DIR}"
test -s "$OUTDIR/build-lock.txt"
test -s "$OUTDIR/aflnet.log"
test -s "$OUTDIR/aflnet-out/fuzzer_stats"
test -s "$OUTDIR/post-smoke/smtp-smoke.json"
grep -q '"status": "pass"' "$OUTDIR/post-smoke/smtp-smoke.json"
test -s "$OUTDIR/v8-coverage-summary.json"
test "$(sed -n 's/^target_version=//p' "$OUTDIR/build-lock.txt")" = 3.4.0
grep -q '^feedback=AFLNet -P SMTP response-state graph' "$OUTDIR/run-method.txt"
python3 - "$OUTDIR" <<'PY'
import json, pathlib, sys
p=pathlib.Path(sys.argv[1])
elapsed=int((p/'fuzz-end-epoch.txt').read_text())-int((p/'external-start-epoch.txt').read_text())
stats={}
for line in (p/'aflnet-out/fuzzer_stats').read_text().splitlines():
    if ':' in line:
        k,v=line.split(':',1); stats[k.strip()]=v.strip()
summary=json.loads((p/'v8-coverage-summary.json').read_text())
assert elapsed >= 20, f'campaign ended too early: {elapsed}s'
assert int(stats.get('execs_done','0')) > 0, 'AFLNet completed no executions'
assert summary['functions_executed'] > 0, 'no Haraka runtime functions were observed'
print(f'ACCEPTANCE_PASS elapsed_seconds={elapsed} executions={stats.get("execs_done")} target_scripts={summary["target_scripts_observed"]} functions_executed={summary["functions_executed"]}')
PY
