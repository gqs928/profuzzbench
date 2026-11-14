# OpenSSL QUIC 4.1.0 baseline

This target benchmarks OpenSSL 4.1.0 using its upstream single-connection server example. AFLNet drives one QUIC Initial datagram at a time over loopback UDP, starting a fresh server process for each testcase. The measured scope is Initial processing and the first server response; it does not cover a completed TLS handshake or HTTP/3 exchange.

Build with ./build.sh; perform preflight with ./preflight-benchmark.sh; run the formal 30-minute campaign with ./run-benchmark.sh. Check source-lock.json, toolchain-lock.json, and ACCEPTANCE.md for scope and provenance. The formal run completed with 11,483 executions and 64 paths, but feedback stability was 19.81% with one variable path, so the result is marked for stability review. The central experience library stays separate from this individual delivery.
