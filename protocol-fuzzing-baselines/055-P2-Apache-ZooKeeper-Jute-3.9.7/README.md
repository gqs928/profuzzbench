# Apache ZooKeeper 3.9.7 — Jute protocol baseline

This profile targets the standalone, unauthenticated, plaintext ZooKeeper client protocol on TCP/2181. It uses the official ZooKeeper 3.9.7 linux/amd64 image pinned by manifest digest. The binary's `zkServer.sh version` output is checked at runtime. ZooKeeper's release page identifies 3.9.7 as the current release; 3.8.8 is the latest release in the separate 3.8 stable branch.

The AFLNet adapter splits the four-byte big-endian Jute length frames. It treats the initial `ConnectResponse` as a different record from ordinary `ReplyHeader` responses, then feeds response/error classes to AFLNet. A narrow AFLNet lifecycle patch skips a no-forkserver busy-wait on exited children until the fuzzer can reap them. Each testcase starts from a fresh standalone server process with empty data and transaction-log directories. The JVM is not coverage-instrumented; AFL's helper bitmap is not ZooKeeper source coverage.

## Build and run

```sh
./build.sh
docker compose --env-file images.env -f compose.yaml run --rm fuzz
```

The container is isolated from external networking and limited to 2 CPUs and 2,300 MiB memory. It uses the official image entrypoint so the JVM runs as the image's `zookeeper` user. The fuzzer receives a harmless Python interpreter placeholder while the separately managed JVM is the actual TCP target.

## Replay and smoke

After the campaign, replay the saved raw streams and AFLNet queues, then run valid client operations and check shutdown:

```sh
docker compose --env-file images.env -f compose.yaml run --rm --entrypoint python3 fuzz \
  /opt/benchmark/replay_queue.py \
  /results/zookeeper-fuzz-30m-YYYYMMDD \
  /results/zookeeper-fuzz-30m-YYYYMMDD/replay-validation 100
docker compose --env-file images.env -f compose.yaml run --rm --entrypoint python3 fuzz \
  /opt/benchmark/zookeeper_smoke.py /results/zookeeper-smoke-post-YYYYMMDD 3
```

The replay records server readiness, sent messages, parsed response states, malformed-input outcomes, and per-sample transport errors separately. This profile excludes quorum/ZAB ports, TLS, SASL, and multi-node consensus.

The pinned target and fuzzer inputs are in `source-lock.json`; release details are at [Apache ZooKeeper releases](https://zookeeper.apache.org/releases/). The centralized `基准化经验库.md` stores cross-protocol automation lessons; this standalone package does not duplicate an experience entry.
