# YugabyteDB 2026.1.3.0 — YCQL Native Protocol baseline

This profile benchmarks one isolated YugabyteDB node through the unauthenticated YCQL Cassandra Native Protocol v4 listener on TCP/9042. The tested product release is **2026.1.3.0, build 100**, pinned by the official linux/amd64 image digest in `images.env` and `source-lock.json`. The server binary is checked at runtime before readiness is accepted.

The target is black-box. AFLNet receives state feedback from Cassandra-compatible native response frames; neither the YugabyteDB server nor its source is coverage-instrumented. The helper bitmap must not be reported as YugabyteDB source coverage. The run clears user keyspaces between testcases while keeping a single server process alive.

## Build and run

```sh
./build.sh
docker compose --env-file images.env run --rm fuzz \
  bash /opt/benchmark/run.sh /results/yugabyte-fuzz-30m-YYYYMMDD 30m
```

The profile is network-isolated, limited to 2 CPUs and 4,300 MiB memory, and uses no forkserver. AFLNet's placeholder process is a harmless Python interpreter command; the separately managed YugabyteDB process is the protocol target. The 30-minute stop wrapper repeats SIGINT until AFLNet flushes its final statistics.

## Replay and smoke

Run the saved raw and AFLNet queues in a separate container, then run valid protocol flows and verify listener shutdown:

```sh
docker compose --env-file images.env run --rm --entrypoint python3 fuzz \
  /opt/benchmark/replay_queue.py \
  /results/yugabyte-fuzz-30m-YYYYMMDD \
  /results/yugabyte-fuzz-30m-YYYYMMDD/replay-validation 100
docker compose --env-file images.env run --rm --entrypoint python3 fuzz \
  /opt/benchmark/yugabyte_smoke.py /results/yugabyte-smoke-post-YYYYMMDD 3
```

The replay summary separates target readiness, protocol responses, and per-sample transport events. It does not treat a peer close, timeout, or request-level decoder error as a server crash without corroborating process and post-run health evidence.

The official release is listed at [YugabyteDB releases](https://github.com/yugabyte/yugabyte-db/releases). This standalone package contains implementation-specific evidence only; cross-protocol automation lessons are maintained in the central `基准化经验库.md`.

