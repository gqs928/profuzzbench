# OpenSMTPD 7.9.0p0 SMTP baseline

This package pins OpenSMTPD 7.9.0p0 (`769f646...`) and the AFLNet source/adapter. It runs the SMTP daemon on loopback TCP 2525 with an isolated local mailbox and no relay rule. Docker runs with `--network none`; the mail configuration accepts only the benchmark's local recipient domain.

AFLNet uses SMTP response-state feedback and an AFL-instrumented client helper. The helper's AFL bitmap and crash counters are not target coverage. The daemon itself is built with GCC coverage counters; the campaign and post-smoke phases flush and summarize OpenSMTPD source coverage separately.

Build from this directory with `docker build -t profuzzbench/opensmtpd-aflnet:7.9.0p0 .`. Pre-create an empty output directory and run a short acceptance pass with:

```sh
mkdir -p results/smtp-smoke
docker run --rm --network none -v "$PWD/results:/work/results" \
  profuzzbench/opensmtpd-aflnet:7.9.0p0 -lc '/work/run.sh /work/results/smtp-smoke 30s'
bash validate.sh results/smtp-smoke
```

The default campaign lasts 1800 seconds. Results include the pinned build lock, configuration check, pre/post SMTP smoke checks, AFLNet state graph and helper metrics, and separate OpenSMTPD GCOV summaries.

## Accepted formal run

The 2026-11-06 campaign completed 1,801 seconds with 1,371 executions, 3 response paths, 100% helper stability, 0.01% helper bitmap, and no helper crashes or hangs. The daemon's independent GCOV summary recorded 1,776/30,060 source lines (5.9%), 161/1,775 functions (9.1%), and 646/17,168 branches (3.8%). The helper bitmap is not target code coverage. The campaign used an isolated local mailbox and accepted SMTP messages without external relay; pre- and post-run delivery smoke checks passed.
