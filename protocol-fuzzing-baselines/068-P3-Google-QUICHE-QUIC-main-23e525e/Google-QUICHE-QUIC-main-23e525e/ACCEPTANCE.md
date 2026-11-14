# Acceptance record

status: complete

Protocol: QUIC v1 over UDP  
Implementation: Google QUICHE main@23e525e5184bbd98d9722bc3bb3f4ce181efcde4, official quic_server example  
Scope: one QUIC v1 Initial datagram and first server packet; no completed TLS handshake or HTTP/3 exchange  
Fuzzer: AFLNet 2.56b with custom QUIC state parser; C++ coverage using AFLNet 2.56b afl-gcc/afl-g++ assembler wrappers
Formal duration: 30 minutes, one campaign at a time  

Seed: 1,200-byte QUIC v1 Initial with a complete TLS 1.3 ClientHello and QUIC transport parameters. Its AEAD and header protection were independently verified. SHA-256: `c6332ee934a5701e00f670618e1e151725be421bce4ea8396e30e24f4983a748`.

Build: `//quiche:quic_server`; binary SHA-256 `524d8f4571d95e8cb1dc3a1729c3c63becfb74e39b9ce579f3823805b567df99`. AFLNet 2.56b `afl-fuzz` SHA-256 `5d806281f6e60f1002a24b5b0b96cbd2bf7fd2f9b3e0f5c4639e28124eff54d9`. Source archive SHA-256 is recorded in `source-lock.json` and the build log.

Preflight: 60.065 seconds; 398 executions, 40 paths, 99.81% stability, 4.43% bitmap coverage, zero crashes and hangs. Three smoke exchanges each returned a 108-byte QUIC Initial. All 40 queue samples started and stopped cleanly with the listener released.

Formal run: supervisor measured 1,800.065 seconds; AFLNet stats span 1,801 seconds. It completed 11,675 executions over 87 paths with 99.40% stability and 4.76% bitmap coverage, with zero crashes and hangs. All 87 queue samples started, remained alive after input, exited cleanly on SIGTERM, and released their listeners. No response was observed for 63 mutated samples; the other replies were classified by QUIC public-header type. Post-run smoke again completed three valid Initial exchanges and confirmed listener release.

Cleanup: after validating a candidate ZIP CRC and SHA-256, removed the dedicated 368 MB image `google-quiche-aflnet-bench:main-23e525e` (`sha256:b8411ecf836c0dcbac38dadb204a12eb832b4429895dd78ff3f37df086d3798e`). Verified the tag and ID are absent; shared Ubuntu and Rocky Linux base images were preserved. No global prune was run.
