# Acceptance record

status: unstable/needs_review

Protocol: QUIC v1 over UDP  
Implementation: Microsoft MsQuic v2.6.4 (`quicsample`, official sample server)  
Scope: one QUIC v1 Initial datagram and first server packet; no completed TLS handshake, sample-stream exchange, or HTTP/3 exchange
Harness adapter: `patches/msquic-quicsample-serve.patch` replaces the sample's stdin/Enter wait with a `pause()` loop because AFLNet sets target stdin to `/dev/null`; MsQuic protocol sources are unchanged.
Fuzzer: AFLNet 2.56b with QUIC UDP-datagram atomic framing and public-header state feedback  
Formal duration: one campaign at a time, 30 minutes

Source and toolchain hashes are in `source-lock.json` and `toolchain-lock.json`. A valid Initial seed must pass seed structure validation and all three preflight network smoke passes before fuzzing. Formal acceptance requires the supervisor deadline, positive coverage-map activity, no unexplained process exit, complete queue replay, clean SIGTERM shutdown, listener release, CRC-checked package, and verified target-image removal.

## Formal campaign result

The 2026-11-13 campaign reached the 1,800-second supervisor deadline (elapsed 1,800.072 s; controlled SIGINT; AFLNet child exit code 0). Final AFLNet metrics: 12,234 executions, 273 total paths, 60.86% stability, 7.04% bitmap coverage, zero unique crashes and zero unique hangs. AFLNet's dry run warned that instrumentation output varies across runs; the low stability therefore fails the profile's stability gate and must not be presented as a stable pass.

The 1,200-byte QUIC v1 Initial was accepted in all three preflight passes and each produced a 1,200-byte Initial response. All 273 queue samples replayed against a fresh target process, stayed alive through controlled cleanup, and released UDP/4567; 265 samples produced no response. This confirms process and listener lifecycle, not complete QUIC handshake coverage. See the result JSON and fuzzer_stats for evidence.

Target image cleanup: the dedicated image ID was removed after candidate ZIP CRC validation; the exact ID is confirmed absent. The failed preflight directory was deleted, the successful preflight and formal result evidence were retained, and the pinned shared Ubuntu base was preserved. Cleanup evidence is in build-logs/cleanup-evidence.json.
