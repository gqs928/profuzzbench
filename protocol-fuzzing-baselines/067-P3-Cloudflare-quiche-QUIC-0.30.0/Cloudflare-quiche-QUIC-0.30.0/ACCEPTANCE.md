# Acceptance record

status: complete

Protocol: QUIC v1 over UDP  
Implementation: Cloudflare quiche 0.30.0 (`quiche-server` example)  
Scope: process one client Initial datagram and return the server's first QUIC response; no completed handshake or HTTP/3 request  
Fuzzer: AFLNet 2.56b with the custom `QUIC` parser and Rust SanitizerCoverage via `cargo-afl`; target AFL++ forkserver in vanilla compatibility mode; coverage map 262,144 bytes  
Formal duration: 1,800.033 seconds, one campaign at a time  

## Evidence

- Locked quiche and AFLNet source archives and patch hashes verified by `package.py`.
- Preflight: 60.006 seconds, 371 executions, 22 paths, 98.95% stability, 5.68% bitmap coverage, no crashes or hangs.
- Formal run: 11,557 executions, 148 paths, 98.49% stability, 6.03% bitmap coverage, 0 crashes, 0 hangs. Deadline wrapper stopped AFLNet with SIGINT; child exited 0 and wrapper reported the requested deadline reached (wrapper exit 124 is the expected timeout indication).
- Before and after each run, three valid 1,200-byte QUIC v1 Initial smoke requests each received a 1,200-byte QUIC v1 Initial response. All target processes remained alive until controlled SIGTERM, exited cleanly, and released UDP/4433.
- Formal queue replay: all 148/148 samples started a fresh target, left it alive after input, exited cleanly on SIGTERM, and released the listener. 102 samples received no response, 35 produced an Initial response, and 11 produced other QUIC long-header responses. Crash and hang replay queues were empty; AFLNet reported 0 of each.
- Preflight queue replay also passed all 22/22 samples. Post-run UDP/4433 rebinding checks passed.
- Removed both quiche image tags and all 8 quiche-project-labeled image IDs; verified all IDs and tags absent and no quiche project image or container remaining. The shared Ubuntu base image was retained.
- Standalone protocol ZIP passed package evidence checks and CRC verification; its SHA-256 sidecar was generated. The central experience library is excluded from the protocol ZIP.

## Reproduction boundary

The target consumes one UDP datagram at a time. This benchmark does not claim to fuzz a full QUIC connection, TLS handshake, or HTTP/3 transaction. A no-response replay is an expected outcome for malformed or incomplete datagrams, provided the server remains alive and cleans up normally.
