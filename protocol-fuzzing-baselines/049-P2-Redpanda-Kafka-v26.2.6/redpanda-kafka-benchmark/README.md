# Redpanda Kafka-protocol benchmark

This profile benchmarks the Kafka native TCP endpoint of Redpanda's latest stable 26.2 line as of 2026-11-11: `v26.2.6`. The target is the official OCI image, pinned by manifest digest and verified in-container with `rpk --version` and `redpanda --version`. The release notes list v26.2.6 as the newest patch release; the official Kafka-compatible protocol path is isolated on loopback inside a `--network none` container.

The profile reuses the locally validated AFLNet Kafka request-frame adapter and its correlation-ID response-state mapping. Every testcase gets a fresh single-node broker process: AFLNet's `-K` sends SIGTERM to the foreground Redpanda process; the next launch clears only `/var/lib/redpanda/data` before restarting. This keeps record/topic history from leaking between inputs. A 5-second startup delay is used before connection, and AFLNet's connection retry is retained.

This is a black-box protocol-state baseline. The published Redpanda binary is not rebuilt with AFL compiler instrumentation; the adapter derives Kafka state feedback from actual broker responses. The ELF launcher has its own helper bitmap, which is recorded only as a fuzzer artifact and must not be presented as Redpanda source coverage. TLS/SASL, replication, multi-broker behavior, Schema Registry, HTTP proxy, and production configuration are out of scope.

## Build and smoke test

Run from this directory:

```sh
./build.sh redpanda-kafka-fuzz-bench
docker run --rm --cpus=1 --memory=2g --memory-swap=2g --network none \
  redpanda-kafka-fuzz-bench python3 /home/redpanda/benchmark/redpanda_smoke.py \
  /tmp/redpanda-smoke 5
```

The smoke test repeats ApiVersions → Metadata → Produce → Fetch in fresh broker processes and then uses `rpk` to produce and consume a real record. Preserve logs and compare normalized API response status/correlation IDs across rounds before formal fuzzing.

## AFLNet run

```sh
docker run --rm --cpus=1 --memory=2g --memory-swap=2g --network none \
  -v "$PWD:/workspace:ro" -v "$PWD/results:/results" \
  redpanda-kafka-fuzz-bench bash /workspace/run.sh /results/fuzz-smoke 120s
```

The formal acceptance flow uses the same launcher/limits with a 30-minute duration, saves `fuzzer_stats`, `plot_data`, `ipsm.dot`, logs and queue replay evidence, and checks that broker health recovers after each testcase. Run exactly one formal campaign at a time. Remove the profile image by its recorded image ID only after its result package has passed checksums.

## Version and scope sources

- [Redpanda v26.2 release notes](https://docs.redpanda.com/streaming/current/reference/releases/redpanda/)
- [Redpanda supported versions](https://support.redpanda.com/hc/en-us/articles/20617574366743-Redpanda-Supported-Versions)
- [Redpanda `rpk redpanda start` reference](https://docs.redpanda.com/streaming/current/reference/rpk/rpk-redpanda/rpk-redpanda-start/)
- [Kafka protocol reference](https://kafka.apache.org/protocol/)
