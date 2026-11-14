# YugabyteDB 2026.1.3.0 — YCQL Native Protocol benchmark acceptance

## Target identity

- Protocol: unauthenticated YCQL Cassandra Native Protocol v4 over TCP/9042.
- Product image: `docker.io/yugabytedb/yugabyte:2026.1.3.0-b100`, linux/amd64 manifest digest `sha256:3d2c008625dbbe06879f96452d22afd39806d80bbcdedaa6364c2a5ae8893469`.
- Product binary: `/home/yugabyte/bin/yb-server --version` reported `2026.1.3.0 build 100`, revision `f2635f5b064c1a8271e432401fbf3809cada776d`.
- Custom benchmark image: `sha256:3efe5b2c14d2bffb6af5af16300b7855829982040d7807d8332c68f1e3a833d2` (2,633,561,975 bytes). It is scheduled for removal after package verification.
- Fuzzer: AFLNet ProFuzzBench snapshot commit `0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732`; source archive SHA-256 is in `source-lock.json`.
- Network was isolated. The container had 2 CPUs, a 4,300 MiB memory limit, and swap disabled.

## Harness and reset contract

The adapter parses Cassandra Native Protocol v4/v5-compatible 9-byte frame headers and maps response opcodes/error codes to AFLNet state feedback. YugabyteDB was not coverage-instrumented. AFLNet's 0.00% bitmap is a helper metric, not YugabyteDB source coverage.

One YugabyteDB process stayed alive through the campaign. The pre-testcase hook dropped all non-system keyspaces and checked the exact product version before accepting readiness. Fuzzer process and target server shared the same 2-CPU/4,300-MiB budget. The placeholder command was an ELF Python interpreter invocation; the separately managed YCQL listener was the protocol target.

## Formal campaign

AFLNet's timer wrapper reached its configured 30-minute boundary and repeated SIGINT until AFLNet exited cleanly and wrote its final statistics. The stats timestamps span 1,803 seconds.

| Metric | Result |
|---|---:|
| Duration from `fuzzer_stats` timestamps | 1,803 seconds |
| Executions | 409 |
| Queue paths | 35 total; 28 found during the campaign |
| `cycles_done` / `pending_total` | 0 / 35 |
| Stability | 100.00% |
| AFL helper bitmap | 0.00%; not YugabyteDB source coverage |
| AFLNet unique crashes / hangs | 0 / 0 |
| Slowest testcase | 7,321 ms |
| Peak fuzzer RSS | 42 MiB |
| Per-testcase timeout | 300,000 ms |
| Deadline stop | SIGINT, 3 attempts, AFLNet return code 0 |

This is a timed initial baseline: the fuzzer did not complete its first queue cycle. The low throughput reflects a server-side keyspace cleanup before each testcase; report execution count and elapsed time together.

## Queue replay

All saved queue samples were replayed in the dedicated `results/yugabyte-fuzz-30m-20261112/replay-validation/` directory: 35 raw queue streams, 35 AFLNet replayable-queue messages, and 32 new-IPSM-path messages. All 102/102 reached version-checked target readiness; 327 request frames were sent and 286 Native Protocol response frames received. There were 41 classified receive outcomes: 24 bounded socket timeouts and 17 peer closes before a 9-byte Native Protocol response header. There were no reset-hook or session errors; YugabyteDB stopped with exit code 0. These incomplete-input outcomes are separate from AFLNet crash/hang counters. Per-sample events and logs are in the replay-validation directory.

## Post-run protocol smoke

Three repetitions of four valid flows passed: release-version query, cluster-name query, keyspace create, and multi-query. All 12 flows passed with 39 Native Protocol responses, and the YCQL listener closed after graceful shutdown. Evidence is in `results/yugabyte-smoke-post-20261112/protocol-smoke.json`.

## Scope and limitations

- Only one unauthenticated plaintext YCQL node was tested; YSQL, TLS, authentication, multi-node consensus, and non-YCQL APIs were excluded.
- AFLNet state feedback is black-box protocol feedback. Neither the YugabyteDB server binary nor its source was instrumented.
- `cycles_done=0`; this is a bounded initial baseline, not full queue convergence.
- The target image ID and benchmark image ID are recorded in the build logs; both are removed after evidence and archive verification.
