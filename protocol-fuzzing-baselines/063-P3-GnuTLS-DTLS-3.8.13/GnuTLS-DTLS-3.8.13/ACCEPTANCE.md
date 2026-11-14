# GnuTLS DTLS baseline acceptance

Status: complete

Target: GnuTLS 3.8.13 (`gnutls-serv`), DTLS 1.2 over local UDP. DTLS 1.0/1.3, TLS/TCP, external services, and uninstrumented production binaries are outside this profile.

## Build and preflight

- The official GnuTLS 3.8.13 source archive SHA-256 and both maintainer signatures were verified during the image build. GNU Nettle 3.10.2 was separately signature- and hash-verified and built because Ubuntu 24.04 supplies Nettle 3.9.1, below the target's minimum.
- Runtime assertions confirmed `gnutls-serv` and `gnutls-cli` 3.8.13; runtime shared-library checks passed.
- Three target-native DTLS 1.2 ClientHello seeds passed record-boundary validation and AFLNet dry-run. The seeds were captured from completed handshakes with distinct SNI values; incompatible TinyDTLS examples were rejected during seed development.
- Pre-run and post-run smoke each passed 3/3 full DTLS 1.2 handshakes and 3/3 echo checks.

## Formal campaign

- AFLNet completed the full 1,800-second deadline. `fuzzer_stats` spans exactly 1,800 seconds (`start_time=1794496601`, `last_update=1794498401`); the supervisor records one SIGINT, deadline reached, and AFLNet return code 0.
- Final stats: 17,529 executions (9.73 exec/s), 286 paths, 20 variable paths, 3 completed cycles, 99.31% stability, 7.03% AFL bitmap coverage, 0 unique crashes, and 0 unique hangs.
- The target and `libgnutls` were built with AFL instrumentation; AFLNet also used its DTLS 1.2 response-state parser. `bitmap_cvg` is the fuzzer's instrumented bitmap metric, not a line-coverage percentage.

## Replay and shutdown

- All 574 files across raw `queue`, KL-framed `replayable-queue`, and KL-framed `replayable-new-ipsm-paths` were examined. 446 samples had valid DTLS record framing; all 446 reached a fresh GnuTLS target and left it alive, producing 1,397 response datagrams/states. The other 128 were classified as local `parse_error` because mutation had corrupted DTLS record lengths/boundaries; they were not sent to the target. No transport, target-exit, oversize, crash, or hang events occurred among replayed samples.
- The replay readiness probe matches the local UDP endpoint column from `ss -lunH`; response collection allows 250 ms for an initial response and continues through 150 ms of quiet after each response.
- Post-run smoke passed 3/3 DTLS handshakes and 3/3 echo checks. `listener-closed.json` confirms no `gnutls-serv` process and no UDP/20220 listener remained.

## Delivery

- The package contains the source lock, verified source/signature material, build/run/replay tools, formal results, queue replay, and this acceptance record. The shared automation-framework experience library remains in the central deliverables directory and is intentionally excluded from this protocol ZIP.
- Final ZIP CRC and sidecar SHA-256 are checked by `package.py`; the version matrix and central version checklist are updated after packaging.
