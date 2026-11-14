# Acceptance record

Status: complete; stable baseline passed and dedicated image removed.

- Implementation: picoquic `v2026.11.12.36f49b7`, commit `36f49b73d532369882d97474ac018655b6739a58`.
- Target: official `picoquicdemo` QUIC server; no target-source patch.
- Scope: one valid client QUIC v1 Initial over UDP per testcase and the first public QUIC response. No completed TLS handshake or HTTP/3 request/response.
- Fuzzer: AFLNet 2.56b, direct invocation of the instrumented demo binary, QUIC UDP datagram framing, 262,144-byte feedback map, fresh target process per testcase.
- Formal duration: one 30-minute campaign after archive hashes, linked-library checks, seed validation, repeated target smoke and a short preflight pass.

The successful 60-second preflight completed in 60.065 seconds with 402 executions, 26 paths, 100.00% stability, 1.13% AFL bitmap, and zero unique crashes/hangs. Three target smoke passes each sent the 1,200-byte QUIC v1 Initial and received a 51-byte Initial response.

The formal campaign completed in 1,800.066 seconds with 11,322 executions, 48 paths, 98.96% stability, 1.25% AFL bitmap, six variable paths, and zero unique crashes/hangs. All 48/48 queue inputs started a fresh server, left it alive after input, exited on controlled SIGTERM, and released UDP/4433. Replay classified 33 no-response inputs, one Initial response, seven short-header responses, and seven Version Negotiation responses. No response is not an AFLNet hang. The AFLNet bitmap is instrumented feedback, not source-line coverage. Scope ends at Initial processing and the first server response; no completed TLS handshake or HTTP/3 exchange is measured.

The first preflight attempt passed all three target smokes but AFLNet exited 127 because the runtime image lacked `libcgraph.so.8`; this attempt is retained under `results/aborted/`. The corrected runtime installs `libcgraph8` and makes final-image `ldd` checks for both AFLNet and picoquicdemo fail the build on unresolved dependencies. The rerun passed. Validate ZIP CRC and SHA-256 before deleting only the exact target-specific image; retain shared base images and build cache. Append automation lessons only to the central experience library.
