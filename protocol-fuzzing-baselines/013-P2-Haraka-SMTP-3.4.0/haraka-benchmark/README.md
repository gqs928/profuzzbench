# Haraka 3.4.0 SMTP baseline

This package pins the Haraka 3.4.0 release (`2e1ea5b...`) and its npm lockfile. It runs the SMTP service on loopback TCP 2525 with an explicit discard queue and a controlled local recipient policy. The container has no network, so test messages cannot be relayed or delivered externally.

AFLNet uses the SMTP response-state graph and an AFL-instrumented SMTP client helper. The helper's AFL bitmap and crash counters describe the helper only; Haraka itself is JavaScript and its runtime source execution is collected separately with Node's `NODE_V8_COVERAGE`. The included report script summarizes observed target scripts and executed functions.

Build from this directory with `docker build -t profuzzbench/haraka-aflnet:3.4.0 .`. Pre-create an empty output directory and run a short acceptance pass with:

```sh
mkdir -p results/smtp-smoke
docker run --rm --network none -v "$PWD/results:/work/results" \
  profuzzbench/haraka-aflnet:3.4.0 -lc '/work/run.sh /work/results/smtp-smoke 30s'
bash validate.sh results/smtp-smoke
```

The default campaign lasts 1800 seconds. Results include the source/build lock, pre/post SMTP checks, AFLNet state graph and helper metrics, and separate Haraka runtime coverage summaries.

## Accepted formal run

The 2026-11-06 campaign completed 1,803 seconds with 1,168 executions, 3 paths, 100% AFL helper stability, 0.01% helper bitmap, and no helper crashes or hangs. Node V8 runtime coverage observed 825 target scripts and 1,341 of 4,387 observed functions executed. The AFL bitmap and crash counters describe only the small AFLNet lifecycle helper; the Haraka coverage figures are collected independently from the running server.
