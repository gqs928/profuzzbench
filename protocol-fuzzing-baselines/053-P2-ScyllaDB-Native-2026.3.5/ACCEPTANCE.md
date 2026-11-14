# ScyllaDB 2026.3.5 — Native Protocol benchmark acceptance

## Target identity

- Protocol: unauthenticated ScyllaDB-compatible Native Protocol v4 over TCP/9042.
- Target image: docker.io/scylladb/scylla:2026.3.5, linux/amd64 manifest sha256:bd9eb6c94044a68ea27d8d382c3a0f267db227e6182ac9f3ad3e65a46b92db0d.
- Official release: ScyllaDB 2026.3.5, announced as a production-ready patch release on 2026-11-09. Release notes: https://forum.scylladb.com/t/release-scylladb-2026-3-5/5575.
- Product version assertion: /usr/bin/scylla --version returned 2026.3.5-0.20261103.76a3b0773cfe.
- CQL compatibility assertion: system.local.release_version returned 3.0.8. This is not the product version.
- Fuzzer: AFLNet ProFuzzBench snapshot 0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732; source archive SHA-256 is recorded in source-lock.json.
- Benchmark image ID: sha256:5c34e9cb5e6057f9a2063d276e40d13680e3acb0c1370871fc692c315d04adea. Official base image ID: sha256:069b5cb51ac4205d0942e8d63062c1f168f0ef01392fca9f78dfa335a1345798. Both were removed after package verification; see build-logs/image-cleanup.txt.
- Network access was disabled. Container limits were 2 CPUs, 3,200 MiB memory, and swap disabled. ScyllaDB used one shard and 1,536 MiB configured memory.

## Harness and reset contract

The parser handles the 9-byte Native Protocol frame header and classifies response states from opcode and error code. The AFLNet target is not instrumented. The 0.00% AFL bitmap belongs to the launcher/helper and is not target source coverage. New response-state paths are retained by the AFLNet state-only adapter.

One ScyllaDB process remains alive through the campaign. Before each testcase, reset-scylla.sh checks the product and CQL compatibility versions, then drops all non-system keyspaces. The profile clears data, commitlog, saved-cache, and hints directories at initial service start. Replay uses the same per-sample keyspace reset contract; it does not restart the process for every sample.

ScyllaDB 2026.3 enables tablets by default. A SimpleStrategy keyspace request fails unless tablets are disabled in the CQL options. The smoke uses the documented tablets = {'enabled': false} option. This compatibility condition is recorded in the central framework experience.

## Formal campaign

The 30-minute timer ran to its configured boundary. fuzzer_stats spans 1,801 seconds from start_time to last_update. The timeout wrapper sent SIGINT at the end, AFLNet flushed final statistics, and the run wrapper accepted timeout exit status 124. The AFLNet output says it stopped during the first cycle; therefore this is a bounded baseline and not a complete queue traversal.

| Metric | Result |
|---|---:|
| Duration from fuzzer_stats timestamps | 1,801 seconds |
| Executions | 668 |
| Queue paths | 34 total; 27 found during the campaign |
| cycles_done / pending_total | 0 / 34 |
| Stability | 100.00% |
| Variable paths | 0 |
| AFL helper bitmap | 0.00%; not ScyllaDB source coverage |
| AFLNet unique crashes / hangs | 0 / 0 |
| Slowest testcase | 7,523 ms |
| Peak fuzzer RSS | 48 MiB |
| Per-testcase timeout | 300,000 ms |

AFLNet printed an error waitpid warning while handling the timer signal, then flushed fuzzer_stats with all 668 executions and the expected timeout status. The ScyllaDB lifecycle log records successful readiness/reset checks until shutdown. The node log includes a nonfatal perf_event stall-detector permission warning with fallback to a POSIX timer and one oversized-allocation warning explicitly described by ScyllaDB as nonfatal. No process crash or hang was reported by AFLNet.

## Queue replay

All saved samples were replayed: 34 raw queue streams, 34 AFLNet replayable-queue KL messages, and 32 replayable-new-ipsm-paths KL messages. All 100 samples reached the target readiness check. Replay received 311 responses: 107 in raw mode and 204 in KL mode. There were 44 classified malformed-input events: 41 receive events (26 peer closes before a 9-byte response header and 15 bounded socket timeouts) and 3 broken-pipe send events. There were no reset-hook errors, session errors, or replay process errors; ScyllaDB stopped with exit code 0. These protocol outcomes are not AFLNet crashes or hangs. Per-sample data and logs are in results/scylla-fuzz-30m-20261111/replay-validation/.

## Post-run smoke

After replay, three repetitions of four valid flows passed: OPTIONS/STARTUP plus release-version, cluster-name, keyspace-creation, and multi-query. All 39 Native Protocol responses had the expected opcode and stream ID. The ScyllaDB listener closed after shutdown. Evidence is in results/scylla-smoke-post-20261112/.

## Scope and limitations

- No authentication, TLS, cluster behavior, Alternator, Cassandra v5-only feature coverage, or ScyllaDB source coverage was measured.
- cycles_done is 0, so the campaign did not finish its first queue cycle. Report it as a timed initial baseline.
- The 3.0.8 CQL release_version is a compatibility string; the tested product release is 2026.3.5 as asserted by the product binary and pinned image.
- Replay receive/send outcomes on malformed inputs are reported separately from target crashes and hangs.
- The custom benchmark image and exact ScyllaDB base image were removed after delivery validation. No broad Docker prune was used.
