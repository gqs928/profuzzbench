# Acceptance record

status: complete

Protocol: QUIC v1 over UDP  
Implementation: ngtcp2 v1.26.0 `examples/osslserver`, OpenSSL QUIC-TLS backend 4.1.0 and nghttp3 1.19.0  
Scope: one valid Initial datagram per testcase and the first server packet; no completed TLS handshake or HTTP/3 exchange  
Fuzzer: AFLNet 2.56b; QUIC UDP datagram framing and public-header response-state feedback; 262,144-byte map  
Formal duration: one 30-minute campaign

The pinned source archive, all submodule archives, AFLNet parser/toolchain adapters, seed and base image are recorded in the lock files. The official `osslserver` target is built with the AFLNet wrappers; ngtcp2 shared libraries are bundled at runtime because that is the upstream example's link form. The OpenSSL command-line utility uses `OPENSSL_CONF=/dev/null` only to create the ephemeral test certificate on the minimal container image.

Preflight completed 60.008 seconds: 378 executions, 24 paths, 97.82% stability, 7.17% bitmap feedback, zero unique crashes/hangs. Three valid Initial smoke exchanges each returned a QUIC Initial, then the server exited under controlled SIGTERM and released UDP/4433. All 24 preflight queue samples replayed with the target alive and listener released; 19 had no response.

The formal supervisor completed in 1,800.067 seconds, sent one SIGINT, and recorded AFLNet child exit code 0. AFLNet's final statistics show 11,575 executions, 53 paths, 97.78% stability, 7.26% bitmap feedback, zero unique crashes and zero unique hangs. The map percentage is AFLNet feedback, not source-line coverage. The startup dry-run reports instrumentation output variation, while the measured stability remains 97.78%; that warning and the exact variability are retained in the fuzzer output/statistics for review.

All 53 formal queue inputs replayed in fresh server processes: 53/53 started, remained alive after input, exited under controlled SIGTERM, and released the UDP listener. The response parser classified 3 Initial responses, 6 short-header responses, 5 Version Negotiation responses, and 39 inputs with no response. The silent cases are reported as no response, not as target hangs. Formal pre/post smoke again passed all three Initial exchanges; listener checks passed after campaign and replay.

Cleanup: candidate ZIP passed CRC and SHA-256 (`565133a9d29bd5b95bed3ebcb627cd7d2b26aa4ca601229cbb1c8e38a69f3f2e`); after confirming no container referenced it, removed only `ngtcp2-aflnet-bench:v1.26.0` (`sha256:4632f2fb80bf491d31dc7c4b149185862f76458115c2d5ee5060a432eb56c0b8`, 241,207,151 bytes). Docker inspection confirmed the image is absent. Shared base images and the 3.607 GB build cache were preserved; no global prune was run. Final standalone ZIP CRC and SHA-256 sidecar are verified by the package tool. The aggregated experience entry remains only in the central experience library.
