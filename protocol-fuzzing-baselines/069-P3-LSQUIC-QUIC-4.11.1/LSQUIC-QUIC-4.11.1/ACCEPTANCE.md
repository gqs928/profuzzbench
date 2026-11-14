# Acceptance record

status: complete

Protocol: QUIC v1 over UDP  
Implementation: LiteSpeed QUIC (LSQUIC) v4.11.1, official `http_server` example  
Scope: one QUIC v1 Initial datagram and first server packet; no completed TLS handshake or HTTP/3 exchange  
TLS: pinned BoringSSL source commit; ephemeral self-signed certificate mapped to SNI `quic.tech`  
Fuzzer: AFLNet 2.56b, custom QUIC public-header state parser, C/C++ target coverage via AFLNet 2.56b `afl-gcc`/`afl-g++` assembler wrappers  
Formal duration: 30 minutes; single campaign

Build: LSQUIC official stable tag `v4.11.1` at `2f4cd42f27cf8e9b0a0f43e376a618ec8ce4a7ff`, with pinned `ls-qpack`, `ls-hpack`, BoringSSL and AFLNet sources. Exact archive and patch SHA-256 values are recorded in source locks. Target binary SHA-256: `aa53d83a6cac535ec6ee2c24ac3f2e2dbff0d13327e695c4bfbc0c7a7a587714`; AFLNet SHA-256: `5d806281f6e60f1002a24b5b0b96cbd2bf7fd2f9b3e0f5c4639e28124eff54d9`.

Seed: one 1,200-byte QUIC v1 Initial containing a complete TLS 1.3 ClientHello and QUIC transport parameters, with independently verified Initial AEAD and header protection; SNI `quic.tech`; SHA-256 `c6332ee934a5701e00f670618e1e151725be421bce4ea8396e30e24f4983a748`.

Preflight: supervisor duration 60.065 seconds; 406 executions, 31 paths, 100.00% stability, 2.15% bitmap coverage, zero crashes/hangs. Three Initial smoke exchanges each returned a 60-byte QUIC Initial. All 31 queue inputs started and exited cleanly with listener release.

Formal campaign: supervisor duration 1,800.065 seconds. AFLNet stats span 1,804 seconds because final stats were written several seconds after deadline shutdown; the monotonic supervisor duration is authoritative. The campaign produced 11,647 executions, 95 paths, 99.80% stability and 2.33% bitmap coverage, with zero crashes and hangs. All 95 raw queue samples started, remained alive after input, exited cleanly on SIGTERM, and released the UDP listener. Sixty mutated samples had no response; remaining replies were classified by public QUIC header type.

Post-run: three valid Initial exchanges returned 60-byte Initial responses; the target exited under controlled SIGTERM and UDP/4433 was released after both smoke and replay. No complete TLS handshake or HTTP/3 exchange was tested.

Cleanup: after validating the candidate ZIP CRC and SHA-256, removed the dedicated 195 MB image `lsquic-aflnet-bench:v4.11.1` (`sha256:1739419ed62705025ce4d03ae94c283776baa01b184a3cd6807ceb0b119d4ee4`). Also removed the two exact untagged intermediate LSQUIC images from failed builds; their IDs and sizes are in `build-logs/intermediate-image-cleanup.json`. Verified the dedicated image is absent. Shared Ubuntu and Rocky Linux base images were preserved; no global prune was run. The final standalone ZIP is CRC-checked and has a matching SHA-256 sidecar.
