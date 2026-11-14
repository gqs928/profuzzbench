# Acceptance record

status: benchmark evidence packaged; stability review required

Protocol: QUIC v1 over UDP  
Implementation: OpenSSL QUIC 4.1.0 (official demos/quic/server/server.c)  
Scope: valid QUIC v1 Initial processing and first server response; no HTTP/3 exchange  
Harness: upstream demo server, no target-source patch  
Fuzzer: AFLNet 2.56b, UDP datagram framing and QUIC public-header state feedback  
Formal duration: one campaign at a time, 30 minutes

Source and toolchain hashes are recorded in the lock files. A valid Initial seed passes structure validation and three target-specific preflight passes. The 60-second preflight reports 100.00% stability. The 30-minute formal campaign completed its deadline with 11,483 executions, 64 paths, 19.81% stability, 4.41% AFL feedback bitmap, one variable path, and zero unique crashes or hangs. All 64 queue samples started the target, left it alive after input, exited on controlled SIGTERM, and released UDP/4433. Because formal stability is below the 90% review gate despite a stable short preflight, this profile is delivered as evidence with status “stability review required,” not as a stable baseline pass. The current review does not attribute the variable feedback to a specific OpenSSL code path.

The first 60-second attempt is retained under `results/aborted/`: QUIC smoke passed, but AFLNet could not load `libcgraph.so.8` and returned 127. The runtime image was rebuilt with `libcgraph8`, and final-image `ldd` checks now cover both AFLNet and the target. A fresh preflight then reached the AFLNet forkserver and completed successfully. Package CRC/SHA validation precedes removal of the exact dedicated image; shared base images and build cache are retained.
