# wolfSSL DTLS 1.2 AFLNet baseline

This completed baseline covers recommendation-order item #65: wolfSSL **5.9.4**, the newest stable release shown by the official release and download pages when checked on 2026-11-12. The official download page publishes SHA-256 `9cd0d69d208d025b16836c177658cc0deebc2a85c4b60898c9bc546bc6cbdf18`; the downloaded source archive matches it. The corresponding upstream stable tag is `v5.9.4-stable` and GitHub marks its signature verified.

The profile targets the official `examples/server` application built together with the AFL-instrumented wolfSSL library. It runs `-u -v 3 -e` for DTLS 1.2/UDP echo and accepts one local client per testcase. DTLS 1.0, DTLS 1.3, TLS/TCP, and external services are excluded. AFLNet's built-in DTLS12 parser supplies request/response state feedback.

## Build and run

```sh
./build.sh
./run-benchmark.sh /results/wolfssl-dtls-fuzz-30m 30m
```

The container was limited to 2 CPUs and 768 MiB. The 30-minute run produced 17,238 executions, 85 paths, 100% stability, 3.43% bitmap, and zero crashes or hangs. Three DTLS handshake-and-echo smoke passes succeeded before and after the run. The full queue replay and listener checks are recorded in the campaign directory; the standalone package excludes the central experience library.

## Pinned inputs

- wolfSSL 5.9.4 source: `source/wolfssl-5.9.4.zip`, checked against the official SHA-256.
- AFLNet ProFuzzBench snapshot: commit `0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732`, with its archive checksum pinned in `source-lock.json`.
- Three DTLS 1.2 ClientHello seeds captured by GnuTLS 3.8.13 from completed local handshakes with distinct SNI values. Their record framing is checked before AFLNet starts and the actual wolfSSL handshake/echo is smoke-tested separately.
- Ubuntu 24.04 is pinned by digest in `images.env`.

The central automation-framework experience library is maintained separately and is not included in this protocol package.
