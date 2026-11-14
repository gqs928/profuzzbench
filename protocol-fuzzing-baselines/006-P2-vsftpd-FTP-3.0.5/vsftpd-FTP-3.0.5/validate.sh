#!/usr/bin/env bash
set -euo pipefail

mkdir -p /work/results/build
python3 /work/validate.py \
  --reference /opt/vsftpd-reference/sbin/vsftpd \
  --instrumented /opt/vsftpd-afl/sbin/vsftpd \
  --config /work/vsftpd.conf \
  --output /work/results/build/service-smoke.json \
  --log /work/results/build/service-smoke.log
/opt/aflnet/afl-fuzz -h > /work/results/build/aflnet-help.txt 2>&1 || test "$?" -eq 1
set +e
timeout --signal=INT --kill-after=10s 30s env AFL_NO_UI=1 AFL_FAST_CAL=1 \
  /opt/aflnet/afl-fuzz -d -i /work/seeds -o /tmp/vsftpd-preflight \
    -N tcp://127.0.0.1/2121 -P FTP -D 20000 -W 100 -w 100000 \
    -t 2500 -m none -x /work/ftp.dict -K -E -R -q 3 -s 3 \
    -- /opt/vsftpd-afl/sbin/vsftpd /work/vsftpd.conf \
    > /work/results/build/aflnet-preflight.log 2>&1
PREFLIGHT_STATUS=$?
set -e
if [ ! -s /tmp/vsftpd-preflight/fuzzer_stats ]; then
  cat /work/results/build/aflnet-preflight.log
  exit 1
fi
if [ "$PREFLIGHT_STATUS" -ne 0 ] && [ "$PREFLIGHT_STATUS" -ne 124 ] && [ "$PREFLIGHT_STATUS" -ne 130 ] \
   && ! { [ "$PREFLIGHT_STATUS" -eq 1 ] && grep -Fq '+++ Testing aborted by user +++' /work/results/build/aflnet-preflight.log; }; then
  cat /work/results/build/aflnet-preflight.log
  exit 1
fi
grep -E '^(execs_done|paths_total|unique_crashes|unique_hangs)[[:space:]]*:' /tmp/vsftpd-preflight/fuzzer_stats \
  > /work/results/build/aflnet-preflight-summary.txt
printf 'timeout_wrapper_status=%s\n' "$PREFLIGHT_STATUS" >> /work/results/build/aflnet-preflight-summary.txt
rm -rf /tmp/vsftpd-preflight
printf 'validation and AFLNet preflight passed\n' >> /work/results/build/service-smoke.log
