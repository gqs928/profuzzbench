# wolfSSL DTLS baseline acceptance

Status: complete

Target: wolfSSL 5.9.4 official `examples/server`, DTLS 1.2 over local UDP. DTLS 1.0/1.3 and TLS/TCP are outside this profile.

## Source and build

- Official wolfSSL 5.9.4 source SHA-256 matches the checksum published by wolfSSL.
- Upstream release tag `v5.9.4-stable` is marked as GitHub-verified.
- Build flags enable DTLS and AFL instrumentation; runtime `wolfSSL_lib_version()` must report 5.9.4.
- The official server example runs in UDP DTLS 1.2 echo mode (`-u -v 3 -e`) with one local client per testcase.

## Preflight and campaign

- Three ClientHello seeds passed DTLS record framing checks and AFLNet dry-run. Three full DTLS 1.2 handshakes and echo responses passed both before and after the formal run.
- The supervisor reached its 1,800-second deadline with one SIGINT; AFLNet exited 0. Stats span exactly 1,800 seconds: 17,238 executions, 85 paths (82 found during the campaign), 26 cycles, 100% stability, 3.43% bitmap, zero crashes, and zero hangs.
- AFLNet used its built-in DTLS12 record/handshake-state parser. The AFL bitmap reflects the instrumented wolfSSL library and example server build, not source-line coverage.

## Replay and shutdown

- All 176 queue entries were classified: 85 raw streams and 91 KL-framed streams. Strict DTLS 1.2 framing excluded 160 malformed entries before target replay (121 wrong-version headers, 18 truncated record headers, 18 record-length overruns, and 3 invalid KL frame lengths).
- All 16 parseable samples reached a fresh wolfSSL server and each received a response datagram. All 16 target processes remained alive after input; there were no replay transport errors or nonzero exits.
- The UDP/20220 listener and server process were confirmed closed after both the campaign and queue replay.

## Delivery

- The standalone protocol ZIP contains the pinned source, scripts, seeds, run metadata, logs, stats, replay evidence, image cleanup record, and this acceptance record. Its CRC and SHA-256 sidecar are checked.
- The central workbook/version checklist and central automation-framework experience library are updated separately. The shared experience library is intentionally excluded from this protocol ZIP.
