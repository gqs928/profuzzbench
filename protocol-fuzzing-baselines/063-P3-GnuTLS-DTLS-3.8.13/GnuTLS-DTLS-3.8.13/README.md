# GnuTLS DTLS 1.2 AFLNet baseline

This package benchmarks the official GnuTLS 3.8.13 release as a local DTLS 1.2/UDP echo server. The release source archive is pinned by SHA-256 and verified against both signatures in the official GnuTLS maintainer keyring. GnuTLS is compiled with AFLNet instrumentation; AFLNet's built-in `DTLS12` parser segments the raw DTLS record stream and applies response-state feedback. The image also builds the signed GNU Nettle 3.10.2 dependency because Ubuntu 24.04's Nettle 3.9.1 does not meet GnuTLS 3.8.13's configure-time minimum.

The profile uses a self-signed local certificate, `gnutls-serv --udp --nocookie --echo`, a fixed DTLS 1.2 priority string, and UDP port 20220. DTLS 1.0, DTLS 1.3, TLS/TCP, and external network services are excluded. AFLNet starts the instrumented server as its target process, so each testcase receives a fresh server instance and the target's forkserver and coverage map stay attached to the same process tree.

The three checksum-pinned seeds are ClientHello datagrams captured from successful handshakes made by the matching GnuTLS client. This matters for state-aware fuzzing: the structurally valid TinyDTLS samples rejected by GnuTLS with `The certificate type is not supported`, leaving AFLNet without response states. The capture helper makes three distinct SNI variants and stores the first flight from each completed handshake.

## Reproduce

```bash
./build.sh
./run-benchmark.sh /results/gnutls-dtls-fuzz-30m-20261112 30m
```

The formal campaign completed 1,800 seconds with 17,529 executions, 286 paths, 20 variable paths, 3 cycles, 99.31% stability, 7.03% AFL bitmap coverage, and 0 crashes/0 hangs. The target is built with AFL instrumentation and uses AFLNet's DTLS12 response-state parser; bitmap coverage is not reported as line coverage. The container limits are 2 CPU cores, 768 MiB memory, and a 10-second testcase timeout. The date-stamped result directory contains the queue, state graph, stats, pre/post smoke, replay report, and listener shutdown evidence; command output is saved in `results/campaign-console.log`.

Full replay examined 574 raw/KL/IPSM files: 446 had structurally valid DTLS record framing and all 446 reached a fresh target, leaving it alive and yielding 1,397 response datagrams/states. The remaining 128 mutated samples were classified as framing `parse_error` before transmission. These parser classifications are separate from target crashes and transport failures.

To regenerate a compatible seed set with the included helper:

```bash
docker compose --env-file images.env -f compose.yaml run --rm --no-deps fuzz \
  python3 /opt/benchmark/capture_seeds.py --output /results/generated-seeds --passes 3
```

Validate queue samples with:

```bash
docker compose --env-file images.env -f compose.yaml run --rm --no-deps fuzz \
  python3 /opt/benchmark/replay_queue.py \
  /results/gnutls-dtls-fuzz-30m-20261112 \
  /results/gnutls-dtls-fuzz-30m-20261112/replay-validation 500
```

The replay checker understands raw DTLS record streams and AFLNet KL-framed replay files. It starts a fresh GnuTLS server per parseable sample, sends each record as one UDP datagram, and records target liveness, response states, framing errors, and transport events. The central automation framework experience library is maintained separately and is intentionally not embedded in protocol delivery ZIPs.
