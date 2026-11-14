# ngtcp2 QUIC benchmark

This target benchmarks the official `examples/osslserver` from ngtcp2 v1.26.0, linked to nghttp3 v1.19.0 and OpenSSL 4.1.0's QUIC-TLS API. ngtcp2 v1.26.0 requires C++23 for its server example; the container therefore pins Ubuntu 26.04 and its GCC toolchain. All upstream source, submodule commits, toolchain, AFLNet parser patch, and seed hashes are recorded in the lock files.

The campaign sends one QUIC v1 Initial UDP datagram per AFLNet input. It records the server's first response and public QUIC header state; it does not claim a completed TLS handshake or an HTTP/3 exchange. The request parser preserves UDP datagram atomicity. The response parser reports public long-header states without decrypting protected frames. The Docker container has no external network and uses two CPUs and 1 GiB of memory.

## Build and run

    ./build.sh
    ./preflight-benchmark.sh
    ./run-benchmark.sh /results/ngtcp2-fuzz-30m-YYYYMMDD 30m

The preflight runs three valid-Initial smoke checks and a 60-second AFLNet trial. The formal campaign is a single 30-minute run. Queue samples are replayed against fresh server processes, and process shutdown plus IPv4/IPv6 UDP listener release are checked after each sample. A dedicated target image is removed only after the candidate package passes CRC and SHA-256 checks; shared base images are retained.

Official references: [ngtcp2 v1.26.0 release](https://github.com/ngtcp2/ngtcp2/releases/tag/v1.26.0), [ngtcp2 v1.26.0 build requirements](https://github.com/ngtcp2/ngtcp2/blob/v1.26.0/README.rst), [nghttp3 v1.19.0 release](https://github.com/ngtcp2/nghttp3/releases/tag/v1.19.0), [OpenSSL 4.1.0 release](https://github.com/openssl/openssl/releases/tag/openssl-4.1.0), and [QUIC v1 RFC 9000](https://www.rfc-editor.org/rfc/rfc9000).
