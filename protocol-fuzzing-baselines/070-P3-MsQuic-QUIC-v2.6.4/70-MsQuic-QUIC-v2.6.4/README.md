# MsQuic QUIC benchmark

This target benchmarks the official MsQuic `quicsample` server built from release `v2.6.4` and its pinned `quictls` submodule. The release tag, source archive, submodule commits, AFLNet patch, toolchain, and seed hashes are recorded in `source-lock.json` and `toolchain-lock.json`.

The campaign sends one QUIC v1 Initial UDP datagram per AFLNet input. It records the server's first response and public QUIC header state; it does not claim a completed TLS handshake, the sample application's stream exchange, or HTTP/3. The seed is the same independently checked 1,200-byte Initial used for the other QUIC v1 targets. Target-specific acceptance and cleanup evidence are in `ACCEPTANCE.md` and `build-logs/`.

The core library and server sample are compiled using AFLNet 2.56b's matching `afl-gcc` / `afl-g++` assembler wrappers. A small, locked harness-only patch keeps the upstream interactive sample alive when AFLNet supplies `/dev/null` as stdin; it does not change MsQuic QUIC handling. The QUIC request parser keeps the whole UDP datagram atomic and the custom response parser reports only public long-header state. The Docker container has no external network and uses two CPUs and 1 GiB of memory.

## Build and run

    ./build.sh
    ./preflight-benchmark.sh
    ./run-benchmark.sh /results/msquic-fuzz-30m-YYYYMMDD 30m

The preflight executes repeated valid-Initial smoke checks and a 60-second AFLNet trial. The formal campaign is a single 30-minute run. Each run replays queue/crash/hang samples against fresh server processes and verifies controlled process exit and UDP listener release. A dedicated target image is removed only after the candidate package passes CRC and SHA-256 checks; shared base images are retained.

Official references: [MsQuic v2.6.4 release](https://github.com/microsoft/msquic/releases/tag/v2.6.4), [MsQuic API sample](https://github.com/microsoft/msquic/blob/v2.6.4/src/tools/sample/sample.c), [MsQuic Linux build documentation](https://github.com/microsoft/msquic/blob/v2.6.4/docs/BUILD.md), and [QUIC v1 RFC 9000](https://www.rfc-editor.org/rfc/rfc9000).
