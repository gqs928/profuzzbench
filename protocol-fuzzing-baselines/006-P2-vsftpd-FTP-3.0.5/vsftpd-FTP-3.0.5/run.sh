#!/usr/bin/env bash
set -euo pipefail

OUT_NAME="${1:-ftp-30m}"
DURATION="${2:-1800}"
OUT_DIR="/work/results/$OUT_NAME"
mkdir -p "$OUT_DIR"
if [ -e "$OUT_DIR/aflnet-out" ]; then
  printf 'refusing to overwrite existing output: %s\n' "$OUT_DIR/aflnet-out" >&2
  exit 2
fi

START_EPOCH="$(date +%s)"
printf '%s\n' "$START_EPOCH" > "$OUT_DIR/external-start-epoch.txt"
set +e
timeout --signal=INT --kill-after=30s "${DURATION}s" \
  env AFL_NO_UI=1 AFL_SKIP_CPUFREQ=1 AFL_NO_AFFINITY=1 \
      ASAN_OPTIONS='abort_on_error=1:detect_leaks=0:symbolize=0:allocator_may_return_null=1' \
  /opt/aflnet/afl-fuzz -d -i /work/seeds -o "$OUT_DIR/aflnet-out" \
      -N tcp://127.0.0.1/2121 -P FTP -D 20000 -W 100 -w 100000 \
      -t 2500 -m none -x /work/ftp.dict -K -E -R -q 3 -s 3 \
      -- /opt/vsftpd-afl/sbin/vsftpd /work/vsftpd.conf \
      >"$OUT_DIR/aflnet.log" 2>&1
FUZZER_STATUS=$?
set -e
END_EPOCH="$(date +%s)"
printf '%s\n' "$END_EPOCH" > "$OUT_DIR/external-end-epoch.txt"
printf '%s\n' "$FUZZER_STATUS" > "$OUT_DIR/wrapper-exit-code.txt"
/work/postprocess.sh "$OUT_NAME" "$DURATION" "$FUZZER_STATUS"
