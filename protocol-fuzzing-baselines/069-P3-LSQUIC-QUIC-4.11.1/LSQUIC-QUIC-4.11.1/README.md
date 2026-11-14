# LSQUIC QUIC baseline

This package benchmarks LiteSpeed QUIC (LSQUIC) v4.11.1, the latest official stable release checked on 2026-11-13. The release tag, source archive, both Git submodules, and BoringSSL source commit are individually pinned and hashed in source-lock.json.

The target is the release's official bin/http_server example, built with AFLNet 2.56b's afl-gcc/afl-g++ assembler wrappers and the release-pinned ls-qpack and ls-hpack submodule commits. A fixed QUIC v1 client Initial carries a complete TLS 1.3 ClientHello, QUIC transport parameters, SNI quic.tech and independently verified Initial protection; the server maps that name to an ephemeral self-signed test certificate.

The benchmark sends each Initial as one UDP testcase and observes the first server packet. It does not claim a completed TLS handshake or HTTP/3 request/response. The AFLNet parser reports public QUIC header states and leaves encrypted frames opaque. The server is loopback-only inside a network-isolated container.

## Build and run

    ./build.sh
    ./preflight-benchmark.sh
    ./run-benchmark.sh /results/lsquic-fuzz-30m-YYYYMMDD 30m

The preflight performs three valid Initial exchanges and a 60-second AFLNet trial. The formal campaign is bounded to 30 minutes. Each run records fuzzer statistics, replays queue/crash/hang samples against fresh server processes, and verifies UDP port release. After acceptance, remove the exact image tag and make the standalone ZIP. The shared 基准化经验库.md stays in the central deliverables directory and is not bundled into this protocol package.

Official references: [LSQUIC v4.11.1 release](https://github.com/litespeedtech/lsquic/releases/tag/v4.11.1), [LSQUIC build instructions](https://github.com/litespeedtech/lsquic/blob/v4.11.1/README.md), and [official source code](https://github.com/litespeedtech/lsquic/tree/v4.11.1).
