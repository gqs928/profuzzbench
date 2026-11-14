# NATS Server 2.15.3 — acceptance record

Status: complete. This profile fuzzes NATS Core client protocol v1 over plaintext TCP/4222 against one standalone, unauthenticated NATS Server 2.15.3 process per testcase. TLS, WebSocket, JetStream, clustering, gateways, leafnodes, and account/JWT flows are excluded. The official target image is pinned to linux/amd64 manifest `sha256:9d85d87039bfba33baf48de4da32a2ee572bcd6c94f6365d05733a672de49253`; the runtime binary reports `nats-server: v2.15.3`. The official target image ID is `sha256:ebabea7c61861e18b8820961301b49fcd7f3df6d9c5db6cc8d0482bef2ef4847`.

## Build and protocol validation

- The AFLNet source snapshot and its no-forkserver, NATS response-state, and endpoint-terminator patches built successfully. The NATS parser test passed, including CRLF framing and PUB/HPUB length handling. The `-N tcp://127.0.0.1/4222` parser accepted 64 repeated checks. Runtime dependency inspection found no missing AFLNet shared libraries, and the target version assertion passed.
- The NATS dictionary loaded all 12 tokens. Core smoke explicitly negotiates `headers: true` in CONNECT before HPUB, and verifies INFO, +OK, MSG, HMSG, PONG and error handling.
- Formal-run prerequisite smoke passed three flows, with 30 server events and successful HPUB/HMSG. The post-run smoke repeated all three flows with 30 events; after shutdown the TCP/4222 listener was closed.

## Formal campaign

The time-bounded AFLNet `-n` campaign ran 1,800 seconds. `fuzzer-deadline.json` records deadline reached, one SIGINT, and child return code 0. Final `fuzzer_stats` records 2,123 executions, 9 cycles, 8 total paths, 100.00% stability, 0 unique crashes, 0 unique hangs, and 0.00% AFL helper bitmap. The NATS Go binary was not coverage-instrumented; the helper bitmap is not NATS source coverage. The run used a fresh server process for each testcase and a 5-second execution timeout.

## Queue replay

All 8 raw queue streams were replayed against fresh NATS processes. There were 0 replay errors and every server exited with code 0. The replay recorded 41 response events: 19 `+OK`, 1 `-ERR`, 1 `HMSG`, 12 `INFO`, 4 `MSG`, and 4 `PONG`. Each record ended at the configured 0.15-second quiet boundary (`quiet-timeout`); that status denotes no further response during the bounded observation window, not a server hang. No target process remained running.

## Reproduction and artifact checks

The archive contains the protocol-specific source locks, input corpus, adapter, build/run/replay/smoke scripts, formal results, post-run validation, and per-file SHA-256 manifest. `package.py` verifies required evidence, ZIP integrity, and that the shared framework experience library is not duplicated in this archive. The SHA-256 sidecar is generated after the archive passes validation. Reusable automation lessons are recorded only in the central `基准化经验库.md`.
