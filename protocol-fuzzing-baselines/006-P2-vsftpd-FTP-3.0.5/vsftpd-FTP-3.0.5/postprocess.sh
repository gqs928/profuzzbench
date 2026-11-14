#!/usr/bin/env bash
set -euo pipefail

OUT_NAME="${1:?output name required}"
REQUESTED="${2:?requested duration required}"
FUZZER_STATUS="${3:?fuzzer status required}"
OUT_DIR="/work/results/$OUT_NAME"
STATS="$OUT_DIR/aflnet-out/fuzzer_stats"
LOG="$OUT_DIR/aflnet.log"

python3 - "$OUT_DIR" "$REQUESTED" "$FUZZER_STATUS" <<'PY'
import pathlib, sys

out = pathlib.Path(sys.argv[1])
requested = int(sys.argv[2])
status = int(sys.argv[3])
stats = out / "aflnet-out" / "fuzzer_stats"
log = out / "aflnet.log"
if not stats.is_file():
    raise SystemExit("AFLNet did not write fuzzer_stats")
log_text = log.read_text(errors="replace") if log.exists() else ""
stopped_by_timeout = status == 1 and "+++ Testing aborted by user +++" in log_text
values = {}
for line in stats.read_text(errors="replace").splitlines():
    if ":" in line:
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip()
elapsed = int((out / "external-end-epoch.txt").read_text()) - int((out / "external-start-epoch.txt").read_text())
start = int(values.get("start_time", "0"))
last = int(values.get("last_update", "0"))
reported = last - start
if status not in (0, 124, 130) and not stopped_by_timeout:
    raise SystemExit(f"AFLNet/wrapper failed with status {status}; inspect {log}")
if elapsed < requested - 10:
    raise SystemExit(f"campaign stopped early: external elapsed={elapsed}s requested={requested}s")
if reported < requested - 20:
    raise SystemExit(f"AFLNet stats cover only {reported}s; requested about {requested}s")
summary = [
    f"external_elapsed_seconds={elapsed}",
    f"fuzzer_stats_seconds={reported}",
    f"requested_seconds={requested}",
    f"timeout_wrapper_status={status}",
    f"aflnet_handled_timeout_sigint={str(stopped_by_timeout).lower()}",
    f"execs_done={values.get('execs_done', 'unknown')}",
    f"paths_total={values.get('paths_total', 'unknown')}",
    f"bitmap_coverage_percent={values.get('bitmap_cvg', 'unknown')}",
    f"stability_percent={values.get('stability', 'unknown')}",
    f"unique_crashes={values.get('unique_crashes', 'unknown')}",
    f"unique_hangs={values.get('unique_hangs', 'unknown')}",
]
(out / "fuzzer-summary.txt").write_text("\n".join(summary) + "\n")
print("\n".join(summary))
PY

COVERAGE_DIR="$OUT_DIR/coverage"
mkdir -p "$COVERAGE_DIR"
find /src/vsftpd-3.0.5 -type f -name '*.gcda' -delete
python3 /work/replay_corpus.py \
  --binary /opt/vsftpd-gcov/sbin/vsftpd \
  --config /work/vsftpd.conf \
  --corpus "$OUT_DIR/aflnet-out/queue" \
  --output "$COVERAGE_DIR/queue-replay.jsonl" \
  --log "$COVERAGE_DIR/replay.log" \
  --timeout "${REPLAY_TIMEOUT:-2.5}"
gcovr --root /src/vsftpd-3.0.5 --filter '.*\.c$' \
  --json-summary "$COVERAGE_DIR/gcov-summary.json" \
  --txt "$COVERAGE_DIR/gcov-summary.txt" \
  /src/vsftpd-3.0.5 > "$COVERAGE_DIR/gcovr.log"
chmod -R a+rX "$OUT_DIR"
