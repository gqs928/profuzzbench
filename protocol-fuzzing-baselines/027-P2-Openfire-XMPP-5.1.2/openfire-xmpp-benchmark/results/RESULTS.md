# Openfire 5.1.2 XMPP baseline results

Run date: 2026-11-09 UTC. Target: official [Openfire 5.1.2 release](https://github.com/igniterealtime/Openfire/releases/tag/v5.1.2), SHA-256 `0f45006e319fb36bf869ef9ca3a3bef930a1bd683a792883b0b0b4c9a3974680`.

## Profile and method

- Transport: plaintext XMPP client-to-server over loopback TCP/5222, domain `example.test`.
- Target config: Openfire embedded database demo boot; admin console disabled; one long-lived JVM service, one new client connection per testcase.
- Fuzzer: AFLNet commit `0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732`, dumb mode, XMPP top-level stanza boundaries and XML response-tag state feedback.
- Formal duration: 1,806 active seconds (the wrapper starts timing after the initial seed dry-run and first mutation testcase).
- Container limit: 1.2 GiB memory, 1 CPU; `--network none` with loopback-only target traffic.

## Formal campaign

| Metric | Result |
|---|---:|
| AFLNet executions | 297 |
| Queue files | 10 |
| New response-state paths | 5 |
| Queue cycles completed | 0 |
| Stability | 100.00% |
| AFL bitmap coverage | 0.00% |
| Unique crashes / hangs | 0 / 0 |

The run did not finish its first queue cycle. The bitmap is zero because this is a black-box Java service and the profile uses response-state feedback rather than Java bytecode instrumentation; this value must not be read as Java source coverage. The result is an exploratory protocol-state baseline with an incomplete queue traversal.

## Post-run checks

- XMPP smoke: `openfire_xmpp_stream=PASS`; stream features response was 1,155 bytes. See `protocol-smoke-final/smoke.log`.
- Queue replay: 10/10 files connected; 6 had a response, 5 encountered a read timeout, and 0 reset/error counts. A response and timeout can both be counted for one sample because replay records whether any bytes arrived and whether the read window later timed out. See `protocol-smoke-final/queue-replay.json`.
- Openfire remained available after the campaign. The startup log includes a hostname-resolution warning under Docker `--network none`; the server completed its database setup and the XMPP smoke passed. See `protocol-smoke-final/server.log`.

Full AFLNet evidence is in `xmpp-30m/` (`fuzzer_stats`, `campaign.log`, `ipsm.dot`, queue, and response regions). The short preliminary smoke runs were diagnostic only and are excluded from the independent delivery ZIP.

## Reproduction

From the package root:

```sh
docker build -t profuzzbench-openfire:5.1.2 .
mkdir -p results/xmpp-30m
docker run --rm --network none --memory=1200m --cpus=1 \
  -v "$PWD/results/xmpp-30m:/results/xmpp-30m" \
  profuzzbench-openfire:5.1.2 \
  bash /opt/benchmark/fuzz.sh /results/xmpp-30m 1800
```
