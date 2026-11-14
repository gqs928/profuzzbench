# Acceptance: Apache ActiveMQ Classic STOMP 6.4.0

Formal AFLNet campaign completed after 1,801 active seconds (requested 1,800 seconds). The active-time clock started when `fuzzer_stats` appeared after the seed dry-run.

Final metrics:

- Executions: 4042
- Paths total / found: 119 / 114
- State-feedback stability: 100.00%
- Unique crashes / hangs: 0 / 0
- Fuzzer exit status / active seconds: 0 / 1801

The live STOMP smoke passed before the campaign. Post-campaign replay covered every queue input: 119 of 119 returned a recognized STOMP response (`CONNECTED`, `MESSAGE`, `RECEIPT`, or `ERROR`), with zero no-response cases and zero connection errors. Replay ran inside the target container network namespace because the host sandbox denies raw TCP sockets. The exact replay counts are in `results/stomp-30m/replay-summary.json`.

This is protocol-state feedback; `bitmap_cvg` is not source-code coverage for this black-box Java broker.
