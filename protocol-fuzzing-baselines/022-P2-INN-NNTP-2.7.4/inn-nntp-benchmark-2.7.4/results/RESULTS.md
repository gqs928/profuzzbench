# INN 2.7.4 formal result

Target: `nnrpd`, NNTP reader protocol, IPv4 loopback TCP/1119. The archive is INN 2.7.4 (`80fc7e801e1996cb17bb430d104dd9c5b29aa571fd4b29a9c821b4fadb051d3b` SHA-256); only the reader-facing command path is in scope.

## 30-minute AFLNet run

- Elapsed window: 1,800 seconds; timeout exit 124 is the expected stop signal.
- Executions: 3,407; queue paths: 141; variable paths: 57.
- Stability: 91.25%; bitmap coverage: 3.77%; `cycles_done`: 0.
- Unique crashes: 0; unique hangs: 0.
- Raw evidence: `nntp-30m/fuzzer_stats`, `nntp-30m/ipsm.dot`, and `formal-run.log`.

The stability value is below 95%, and the initial queue cycle was not complete. Use this as an exploratory baseline rather than a deterministic coverage claim.

## Coverage replay

All 141 queue samples connected to the gcov-enabled `nnrpd`; the replay reported 0 errors and 0 timeouts. The `nnrpd` source report covered 1,002 of 5,172 lines (19%). The report and preserved raw gcov data are in `formal-coverage/`.

The container writes gcov output as the unprivileged benchmark user. The validation and replay commands therefore need supplemental group 9 (`--group-add 9`) so the host-mounted output remains writable. The first replay attempt without that group is retained under `diagnostics/`.
