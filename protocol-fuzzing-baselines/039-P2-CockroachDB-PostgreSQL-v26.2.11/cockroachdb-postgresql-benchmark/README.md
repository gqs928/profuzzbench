# CockroachDB PostgreSQL-wire protocol benchmark

This profile targets CockroachDB's PostgreSQL-compatible frontend/backend wire endpoint, not CockroachDB's internal Raft/RPC protocols. It pins the newest stable self-hosted release available on 2026-11-10: `v26.2.11`. The vendor's 2026-11-03 announcement says 26.4 was available on selected Cloud clusters, with self-hosted binaries following about two weeks later, so 26.4 was not yet a usable self-hosted benchmark target on the verification date.

The official image runs a single-node insecure cluster bound to localhost. Docker host networking is used because the single-node command requires a loopback listen address; this keeps SQL and admin endpoints on host loopback and avoids publishing a container port. This mode is only for isolated testing.

The AFLNet adapter uses PostgreSQL 3.0 StartupMessage and backend-message framing. Seeds issue read-only SQL so state does not accumulate across queue replay. AFLNet runs in network-only protocol-state feedback mode (`-n -E`); the official image is not compiler-instrumented, so `bitmap_cvg` is not source-code coverage and is reported as such.

## Build and run

```sh
./build-aflnet.sh
./start-server.sh
python3 protocol_smoke.py
./fuzz.sh results/cockroachdb-pgwire-30m 1800
python3 replay_queue.py results/cockroachdb-pgwire-30m
python3 protocol_smoke.py
```

After verifying the delivery ZIP and SHA-256, remove the dedicated container and official image with `./stop-server-and-remove-image.sh`.

The shared framework experience library is maintained outside this package.
