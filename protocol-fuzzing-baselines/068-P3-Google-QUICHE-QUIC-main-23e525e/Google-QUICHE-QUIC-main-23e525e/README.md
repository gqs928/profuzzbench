# Google QUICHE QUIC baseline

This package targets the standalone Google QUICHE server at //quiche:quic_server. Google QUICHE publishes no versioned stable release in the repository releases page, so this baseline pins the official main commit 23e525e5184bbd98d9722bc3bb3f4ce181efcde4, checked on 2026-11-13. The source archive and Bazel checksums are recorded in source-lock.json.

The official QUICHE README documents standalone Linux binaries and the quic_server target. This benchmark feeds QUIC v1 Initial datagrams over UDP and observes the server's first packet response. It does not claim a completed TLS handshake or HTTP/3 request/response. The protocol-state parser reads the public QUIC header only; encrypted frames remain opaque.

The pinned QUIC v1 Initial contains a complete TLS 1.3 ClientHello with QUIC transport parameters. It was built from a Python/OpenSSL TLS ClientHello, then wrapped with QUIC v1 Initial AEAD and header protection; the packet protection was independently checked and Google QUICHE returned an Initial response on three consecutive smoke passes. Its SHA-256 is locked in `source-lock.json`. The server uses a self-signed localhost certificate generated at image build time. The benchmark process is loopback-only inside a network-isolated container.

The C++ target is compiled with AFLNet 2.56b's own afl-gcc/afl-g++ assembler wrappers. The shared map is fixed at 262,144 bytes and AFLNet's QUIC parser preserves each UDP datagram as one request region. This keeps the target's vanilla forkserver runtime matched to the same AFLNet 2.56b fuzzer without relying on its legacy LLVM pass API.

## Build and run

    ./build.sh
    ./preflight-benchmark.sh
    ./run-benchmark.sh /results/google-quiche-fuzz-30m-YYYYMMDD 30m

The preflight performs three valid Initial exchanges and a 60-second AFLNet trial. The formal campaign is bounded to 30 minutes. Each run records startup and shutdown checks, replays queue/crash/hang samples against fresh server processes, and verifies UDP port release. Review ACCEPTANCE.md after execution, remove the exact dedicated image, then create the standalone ZIP. The shared 基准化经验库.md remains in the central deliverables directory and is not copied into this protocol ZIP.

Official references: [Google QUICHE README](https://github.com/google/quiche/blob/main/README.md), [official source commit log](https://quiche.googlesource.com/quiche/+log/HEAD), and [QUICHE build target](https://github.com/google/quiche/blob/main/quiche/BUILD.bazel).
