# Leafnode 1.12.0 formal result

Target: the Leafnode NNTP listener harness, IPv4 loopback TCP/1119. The listener launches a fresh protocol session against the local spool fixture; no upstream news service is involved. The source archive SHA-256 is `8310b78006a2088b82dcf9a6b18504ec4f7279bd1047af58d3dac5aaf607ce58`.

## 30-minute AFLNet run

- Elapsed window: 1,800 seconds; timeout exit 124 is the expected stop signal.
- Executions: 2,999; queue paths: 100; variable paths: 2.
- Stability: 18.50%; bitmap coverage: 1.08%; `cycles_done`: 0.
- Unique crashes: 0; unique hangs: 0.
- Raw evidence: `nntp-30m/fuzzer_stats`, `nntp-30m/ipsm.dot`, and `formal-run.log`.

Stability was very low and the initial queue cycle was not complete. Report this as an exploratory result; do not use it as a stable path-coverage estimate.

## Coverage replay

All 100 queue samples connected to the gcov-enabled listener. Three malformed inputs caused Leafnode to reset the peer while the replay drained the response; the harness records these target-side closes separately. There were 0 connection or replay errors. The coverage report covered 768 of 5,982 source lines (12.8%) and 419 of 4,749 branches (8.8%). See `formal-coverage/replay.json`, `coverage.txt`, and `gcovr.log`.
