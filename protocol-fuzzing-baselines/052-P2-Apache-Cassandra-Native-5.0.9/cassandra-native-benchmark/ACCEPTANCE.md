# Apache Cassandra 5.0.9 — Native Protocol benchmark acceptance

## Identity and inputs

- Protocol scope: unauthenticated Cassandra Native Protocol v4 over TCP port 9042.
- Target: official `cassandra:5.0.9` image, linux/amd64 manifest digest `sha256:7e2afd76d5afb991f64c5d9be7d1f8abf749e7ab0e9daaccfd6e865efcece7cc`; runtime query `system.local.release_version` returned `5.0.9`.
- Version check: Apache lists 5.0.9 as the current GA release on the [official Cassandra downloads page](https://cassandra.apache.org/_/download.html); checked 2026-11-11.
- Benchmark image ID: `sha256:a313e90d17b791eff9e19300ef3fa0d511f523a28c1cb9e8d8da84e2bf70ee83` (removed after verification).
- Fuzzer: AFLNet ProFuzzBench snapshot `0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732`; source archive SHA-256 `251f24bf2dddb8118eab56ef2b90c92b06f67c096c62543659eaaf31a31d955d`.
- Host kernel: `7.0.12+kali-amd64`. Cassandra ran successfully in the pinned container; the MongoDB 9.0.8 kernel safety refusal is a separate target-specific constraint.

## Adapter, feedback, and reset contract

The adapter parses Cassandra's 9-byte Native Protocol v4/v5 frame header and extracts response states by opcode and server error code. The campaign uses AFLNet state-only mode with a queue-admission patch that retains new response-state paths even when the helper bitmap has no new bits. Cassandra is not coverage-instrumented: `bitmap_cvg=0.00%` is an AFL helper metric and is not Cassandra source coverage.

One isolated Cassandra JVM remains up during the campaign. At campaign start the script clears data, commitlog, saved-cache, and hints directories. Before each input it queries `system.local` for version 5.0.9 and drops every non-system keyspace. Queue replay uses the same logical reset boundary. It therefore validates replay under the campaign reset contract, not against a new JVM per queue item.

The AFLNet no-forkserver path had a cleanup busy-loop after the initial seed because it waited for the fuzzer parent to reap a zombie helper before returning to `waitpid()`. The build adds a narrow guard to let `run_target()` reap that helper. A 10-second post-fix preflight advanced two executions and wrote readable results. A prior 60-second preflight that used the unpatched binary is excluded from benchmark evidence.

## Formal campaign

The 30-minute timer ran to completion. `fuzzer_stats` spans 1,802 seconds from start to final update. AFLNet's timer delivered SIGINT at the end; the wrapper accepted timeout exit code 124 and stopped Cassandra. The fuzzer printed a `waitpid` warning during signal cleanup, but flushed its final stats and exited under the timeout wrapper.

| Metric | Result |
|---|---:|
| Executions | 418 |
| Queue paths | 28 total |
| `cycles_done` | 0; first queue cycle incomplete |
| Stability | 100.00% |
| Variable paths | 0 |
| AFL helper bitmap | 0.00%; not target code coverage |
| AFLNet unique crashes / hangs | 0 / 0 |
| Container CPU / memory limit | 2 CPU shared by fuzzer and Cassandra / 2,048 MiB |
| Per-testcase timeout | 300,000 ms |

The benchmark is a bounded initial baseline, not a completed queue traversal. Response-state paths grew from the seven initial seeds to 28 total paths.

## Queue replay and exception findings

The replay covered all 81 saved samples: 28 raw `queue` streams, 28 AFLNet `replayable-queue` KL messages, and 25 `replayable-new-ipsm-paths` KL messages. All 81 reset hooks reached the 5.0.9 node; the replay received 262 responses and recorded 10 receive events (4 bounded timeouts and 6 connection resets). Replay target stop exit code was 0.

The formal Cassandra log contains 18 `Unexpected exception during request` decoder entries: 17 `ArrayIndexOutOfBoundsException` and one `IndexOutOfBoundsException`. The fuzz run's unique process-crash counter remained 0; these are request-level decoder exceptions and client-channel disconnects, not target-process crashes. The replay log separately reproduced the same opcode-index `ArrayIndexOutOfBoundsException` three times from the saved inputs below. Each exception was followed by successful service readiness/reset, and the post-replay smoke passed.

| Saved sample | Encoding | Size | SHA-256 | Replay outcome |
|---|---|---:|---|---|
| `id:000012,ipsm` | Raw stream | 43 B | `657dd8e4de9c422268ce644b7a6e4bc20f41062c61c34a1403ccddbca60c1f0b` | 1 response, then connection reset and decoder exception |
| `id:000012,ipsm` | KL messages | 51 B | `69a552b1bd1532d7dd166eafcf5c058ad73087dc521e2a841cf9df019e72c5e4` | 1 response, then connection reset and decoder exception |
| `id:0-6:new` | KL messages | 51 B | `69a552b1bd1532d7dd166eafcf5c058ad73087dc521e2a841cf9df019e72c5e4` | 1 response, then connection reset and decoder exception |

The reproduced stack ends at `org.apache.cassandra.transport.Message$Type.fromOpcode` (`Message.java:125`), with `ArrayIndexOutOfBoundsException: Index -1 out of bounds for length 17`. This is a reproducible server-side protocol decoder exception in Cassandra 5.0.9; no CVE or security impact is asserted here. The server stayed alive and subsequent valid queries succeeded.

## Post-run smoke and cleanup

After the full replay, a fresh node passed four Native Protocol flows (OPTIONS/STARTUP plus release-version, cluster-name, create-keyspace, and multi-query), received 13 responses with matching stream IDs, stopped cleanly, and closed port 9042. Evidence is in `results/cassandra-smoke-post-30m/`.

After evidence collection, the exact custom benchmark image and Cassandra 5.0.9 base image were removed. Before cleanup there were no containers; both image IDs were deleted by exact tag, and the follow-up exact listing returned no Cassandra benchmark images. No broad prune command was used. `build-logs/image-cleanup.txt` records the commands and check. Rebuild instructions and source/parser checks remain in this package.

## Scope and limitations

- No TLS, authentication, Cassandra v5-only request set, cluster behavior, or Cassandra source coverage was measured.
- `cycles_done=0`; the 30-minute queue was not fully traversed.
- The three saved-input decoder exceptions are reproducible request-level exceptions with connection resets, while the service remains available. Treat them separately from AFLNet's process-crash and hang counters.
- The 10 receive events include incomplete/malformed protocol samples; per-sample observations and logs are in `results/cassandra-replay-full-20261111-v2/`.
