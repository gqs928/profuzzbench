# picoquic QUIC baseline

This profile targets the upstream picoquic `picoquicdemo` server from release `v2026.11.12.36f49b7`, built with AFLNet instrumentation. The profile sends one protected QUIC v1 Initial UDP datagram per testcase and records the first public QUIC response. It does not complete TLS or test HTTP/3 transactions.

Build with `./build.sh`, run the 60-second isolated preflight with `./preflight-benchmark.sh`, and run the formal 30-minute campaign with `./run-benchmark.sh`. The pinned picoquic, PicoTLS, picotest gitlink, AFLNet and seed inputs are listed in `source-lock.json`; the base image and toolchain profile are in `toolchain-lock.json`.

The target command directly launches the instrumented `picoquicdemo` binary with the official server CLI options. Each testcase uses AFLNet's `-K` server-reset behavior. The completed formal run recorded 11,322 executions, 48 paths, 98.96% stability, and 1.25% AFL feedback bitmap, with zero unique crashes/hangs; `ACCEPTANCE.md` includes response classification and the first failed preflight attempt. The aggregated automation experience remains in the central experience library and is not included in this individual ZIP.
