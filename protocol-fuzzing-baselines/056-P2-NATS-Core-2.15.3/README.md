# NATS Server 2.15.3 — Core client protocol baseline

This profile targets the stable NATS Server 2.15.3 release over plaintext TCP/4222. The target executable is copied from the official pinned `nats:2.15.3` linux/amd64 image and checked with `nats-server -v` at runtime. On 2026-11-12, the upstream release page lists v2.15.3 as the stable release; this profile does not use the adjacent release candidate.

The AFLNet adapter treats NATS control lines as CRLF-delimited records and preserves the byte-counted payload plus trailing CRLF for `PUB` and `HPUB`. Clients declare `headers:true` in `CONNECT` before HPUB; smoke and seeds exercise this negotiated capability. Response-state feedback distinguishes the server-first `INFO`, `+OK`, `-ERR`, `PING`/`PONG`, `MSG`, and `HMSG` events. Parser tests include payload bytes containing CRLF. The build applies a narrow no-forkserver child-reaping fix and NUL-terminates AFLNet's network endpoint buffer before parsing it; both fixes are pinned and tested before the formal run. The official NATS image is scratch-based, so the pinned official server binary is copied into a small Debian runtime that supplies AFLNet, Python validation tools, and the required runtime libraries.

## Build and run

```sh
./build.sh
docker compose --env-file images.env -f compose.yaml run --rm --pull never --no-deps fuzz \
  /bin/bash /opt/benchmark/run.sh /results/nats-fuzz-30m 30m
```

The container is isolated from external networks and limited to 2 CPUs and 1,500 MiB. AFLNet launches a new standalone NATS process per testcase and terminates it with SIGTERM; Core NATS has no persisted message state in this profile. The NATS executable is not coverage-instrumented, so the AFL helper bitmap is not source coverage.

## Validation

```sh
docker compose --env-file images.env -f compose.yaml run --rm --pull never --no-deps fuzz \
  /bin/bash /opt/benchmark/smoke.sh /results/nats-smoke-post-YYYYMMDD 3
docker compose --env-file images.env -f compose.yaml run --rm --pull never --no-deps fuzz \
  python3 /opt/benchmark/replay_queue.py /results/nats-fuzz-30m-YYYYMMDD/queue \
  /results/nats-fuzz-30m-YYYYMMDD/replay-validation 0
```

The scope is the standalone, unauthenticated Core NATS client protocol. TLS, WebSocket, JetStream, clustering, gateways, leafnodes, and account/JWT authorization are excluded. The [NATS Server release page](https://github.com/nats-io/nats-server/releases) and [official client protocol reference](https://docs.nats.io/reference/protocols/client) document the selected version and wire protocol. Cross-protocol automation lessons belong only in the shared `基准化经验库.md`, not in this protocol package.
