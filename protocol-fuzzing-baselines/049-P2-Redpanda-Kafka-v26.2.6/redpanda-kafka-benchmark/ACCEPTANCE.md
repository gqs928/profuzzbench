# Redpanda Kafka benchmark acceptance

## Locked target

- Target: Redpanda `v26.2.6`, the latest stable patch listed in the official release notes as of 2026-11-11.
- Official image: `docker.redpanda.com/redpandadata/redpanda:v26.2.6@sha256:8b1076e0d61bfceb66594dc01536427ce0b529f8ead35fdab9763ab6085891ce`.
- Runtime checks: `rpk version` and `redpanda --version` both report `v26.2.6`, revision `06e1aca30b726c8de9dc9db5c2b83b4da8edf6d0`.
- Fuzzer: ProFuzzBench AFLNet commit `0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732`; Kafka request/response parser unit test passes.
- Build: Debian package inputs are pinned to snapshot `20261020T213255Z`; the official Redpanda image is pinned by digest. Target source and binary are not modified.

## Formal campaign

The single-node Kafka listener ran in a container with 1 CPU, a 2 GiB memory limit, swap disabled, and `--network none`. Redpanda used one broker core, a 1 GiB ephemeral data tmpfs, and a fresh process with its data directory cleared for every testcase. AFLNet's `-K` terminated the foreground broker between inputs.

| Metric | Result |
|---|---:|
| Elapsed campaign time | 1,800 seconds |
| Executions | 974 |
| Queue paths | 10 |
| IPSM states / transitions | 7 / 8 |
| Stability | 100.00% |
| Unique crashes / hangs | 0 / 0 |
| AFL bitmap coverage | 0.00% |
| Peak resident memory | 213 MiB |

The AFL bitmap is not Redpanda source coverage. This is a black-box protocol-state baseline: AFLNet's state feedback comes from Kafka responses and correlation IDs. The target binary is uninstrumented, and no Redpanda code coverage is claimed.

## Replay and protocol smoke

- Original AFLNet queue: 10/10 inputs replayed; all 10 fresh brokers became ready and every listener closed after the target process stopped. Seven inputs returned 14 valid Kafka response frames; the remaining inputs were malformed, unsupported, or intentionally truncated.
- AFLNet `replayable-queue`: 10/10 inputs replayed; 14 valid response frames, 0 malformed response frames, 0 replay transport errors.
- AFLNet `replayable-new-ipsm-paths`: 7/7 inputs replayed; 14 valid response frames, 0 malformed response frames, 0 replay transport errors.
- Each of the 27 replay cases used a fresh broker process and cleared single-node data directory. The two AFLNet replay directories encode each packet as a 4-byte little-endian length followed by packet bytes; `replay_queue.py` strips those framing prefixes before sending. The ordinary `queue/` files are raw Kafka request streams.
- Post-campaign smoke: 5/5 fresh-process rounds completed ApiVersions, Metadata, Produce, and Fetch; normalized API sequence was stable. `rpk` created a topic, produced a marker record, and consumed it in every round.

## Scope and retained evidence

The benchmark covers one unauthenticated Kafka-compatible TCP broker in dev-container mode. TLS/SASL, replication, multiple brokers, Schema Registry, HTTP Proxy, and production cluster configuration are out of scope. The result archive retains the formal `fuzzer_stats`, `plot_data`, IPSM graph, raw queue and replayable queue data, replay JSON/logs, five-round smoke JSON/logs, build log, version checks, and source checksums.

Official version source: [Redpanda v26.2 release notes](https://docs.redpanda.com/streaming/current/reference/releases/redpanda/).
