# FerretDB 2.7.0 — MongoDB Wire Protocol benchmark acceptance

## Identity and immutable inputs

- Protocol: MongoDB Wire Protocol, OP_MSG only.
- Target: FerretDB v2.7.0 official production binary, commit `0d5eb3343a50b800634cc08ace608bb6f3a3f74b`.
- Target image (linux/amd64): `ghcr.io/ferretdb/ferretdb:2.7.0@sha256:5706414241eb84f0515512c37b46db0f1b1eac9e5ceb7e4c2523211c184b1985`.
- Matched backend: PostgreSQL 17 with DocumentDB v0.107.0-ferretdb-2.7.0; image `ghcr.io/ferretdb/postgres-documentdb:17-0.107.0-ferretdb-2.7.0@sha256:2386795ec2aa7ae559304361979f1dc5708d383ee9020ae63dadc2940dfe58f7`.
- Build base: `debian:trixie-slim@sha256:a72b4433de1cf7d6bae0c4cee74d0547f58601a643b3375f070c51600d63b6b2`.
- Fuzzer: AFLNet ProFuzzBench snapshot `0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732`; source archive SHA-256 is recorded in `source-lock.json`.
- Release check date: 2026-11-11. FerretDB is checked against the official [release page](https://github.com/FerretDB/FerretDB/releases) and [Docker installation guide](https://docs.ferretdb.io/installation/ferretdb/docker/).

## Harness and reset contract

AFLNet's MongoDB parser splits little-endian 16-byte message frames and assigns response states from OP_MSG `ok` and server error codes. Each testcase runs against a fresh FerretDB process. Before the next process, the profile enumerates MongoDB databases and calls `documentdb_api.drop_database()` for each one in PostgreSQL database `postgres`, preserving installed extensions and scheduler state. Authentication is explicitly disabled; authentication negotiation is outside this profile's scope.

FerretDB's Go production binary is not AFL-instrumented. The harness therefore uses AFLNet's no-instrumentation mode and a small AFLNet queue-admission patch: retain an input when it discovers a new MongoDB response-state sequence, even if the helper bitmap is unchanged. This records protocol-state exploration; it does not produce FerretDB source coverage.

## Formal run

The campaign used the configured 30-minute timer, a 30,000 ms testcase timeout, one CPU for the fuzzer, 1,280 MiB for the fuzzer container, 0.5 CPU and 768 MiB for the DocumentDB backend, and disabled swap. `timeout` delivered SIGINT when the timer expired. AFLNet then completed its shutdown and final-stat flush; the `fuzzer_stats` start-to-final-update timestamps span 1,872 seconds (31m12s), including this stop/flush interval. The run wrapper accepted timeout exit code 124 as the expected end of the time-bounded campaign.

Final `fuzzer_stats` values:

| Metric | Result |
|---|---:|
| Executions | 1,506 |
| Queue paths | 24 total; 17 found during the campaign |
| IPSM | 4 response states; 10 observed directed edges |
| Stability | 100.00% |
| AFL helper bitmap | 0.00% |
| Unique crashes / hangs | 0 / 0 |
| Variable paths | 0 |
| Maximum depth | 4 |
| Testcase timeout | 30,000 ms |
| Peak fuzzer RSS | 58 MiB |

Average throughput over the 1,800-second timer is approximately 0.84 executions/second. The final queue was not fully traversed (`cycles_done=1`, `pending_total=21`). The slow process restart and database reset are included in each testcase's cost.

## Replay and post-run checks

A fresh FerretDB process and database reset were used for each of 67 saved samples: raw `queue` 24, AFLNet `replayable-queue` 24, and novel `replayable-new-ipsm-paths` 19. The replay parser treats raw TCP streams and AFLNet's four-byte little-endian length-prefixed message format separately.

The replay received 216 MongoDB responses: 138 successful command replies and 78 protocol/server error replies. Thirty-one samples ended in a classified receive event: 23 server-side connection closes and 8 bounded 10-second receive timeouts; there were no send errors or replay process failures, and all 67 FerretDB processes exited cleanly. These are protocol outcomes for generated malformed/incomplete sequences, not AFLNet-reported crashes or hangs. Per-sample data and logs are in `results/fuzz-30m/replay-validation/`.

After replay, the post-fuzz smoke launched 15 fresh FerretDB processes (three repetitions over five valid MongoDB command flows). It received 36 successful replies; every reply was `ok: 1`, and every listener closed after its process exited. Evidence is in `results/smoke-post-fuzz/`.

## Scope and limitations

- This profile covers unauthenticated MongoDB OP_MSG command exchanges against FerretDB backed by DocumentDB. It does not cover authentication, TLS, the complete MongoDB command surface, or FerretDB internals.
- AFLNet's bitmap is a helper/launcher metric only. No FerretDB source-coverage result was collected; do not present `bitmap_cvg=0.00%` as target coverage.
- The single formal campaign completed one cycle and left 21 pending paths, so the measured state set is an initial baseline rather than an exhaustive protocol-state inventory.
- The baseline relies on a custom AFLNet response-state queue-admission change. Preserve that patch and its source checksums when reproducing the run.
