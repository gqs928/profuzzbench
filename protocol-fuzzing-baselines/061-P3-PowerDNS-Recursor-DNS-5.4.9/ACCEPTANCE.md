# Acceptance — PowerDNS Recursor 5.4.9 DNS/TCP

## Locked target and build

- Target: PowerDNS Recursor 5.4.9, package `5.4.9-1pdns.ubuntu24.04`, from the signed official `noble-rec-54` repository. Repository signing key fingerprint: `9FAAA5577E8FCF62093D036C1B0C6205FD380FBB`.
- Runtime `pdns_recursor --version` reports 5.4.9; `dpkg-query` reports the exact locked package version. Build output is retained in `build-logs/build.log`, `pdns-version.txt`, and `pdns-package-version.txt`.
- Runtime base is Ubuntu 24.04 amd64, pinned to manifest digest `sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852`. AFLNet source commit `0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732` is archive-hash locked.
- Adapter build checks passed: 64 repeated AFLNet `-N` endpoint parser invocations; DNS/TCP two-byte length-prefix, multi-message response-state and truncation parser unit; patched AFLNet binary exposes `DNS_TCP`; runtime dependencies resolve. PowerDNS config check passed.

## Scope and readiness

The profile sends DNS over TCP with RFC 7766 two-byte big-endian length prefixes to a local immutable `fuzz.test` auth-zone on port 5300. External recursion is not used. UDP, TLS, DNSSEC signing, AXFR, dynamic update and forwarding are outside scope. PowerDNS auth-zone responses do not set AA; readiness checks use response ID, QR, RCODE and answer contents instead.

The 20-second preflight completed with deadline reached, child return code 0, 21 executions, 8 paths and no crash/hang. Its 0% stability is expected for this short dry-run and is not reported as a formal stability result.

## Formal campaign

- Results: `results/pdns-recursor-fuzz-30m-20261112/`.
- `fuzzer_stats` spans 1,798 seconds (`start_time=1794483185`, `last_update=1794484983`). The deadline supervisor recorded `deadline_reached=true`, one SIGINT and child return code 0.
- AFLNet completed 2,357 executions, 8 paths, 7 cycles, 100% stability, 0 variable paths, 0 crashes and 0 hangs. `bitmap_cvg=0.00%` is the helper bitmap only and is not PowerDNS source coverage.
- Each testcase stops and restarts the isolated Recursor process and waits for a real DNS/TCP readiness query. This reset/start cost is included in the reported throughput; the resulting rate is about 1.31 executions/second.

## Queue replay and post-run smoke

- Queue replay processed 18 raw or KL-framed samples: 18/18 passed readiness and returned one parsed DNS response each; 0 samples had replay events. RCODE counts were 15 NOERROR and 3 NXDOMAIN. The replay target stop hook returned 0. Evidence is in `replay-validation/replay-summary.json` and per-sample logs.
- Post-run smoke passed 12 queries across three passes (A, AAAA, MX and expected NXDOMAIN for a missing name); the Recursor listener was confirmed closed on `127.0.0.1:5300` after stop.

## Delivery and cleanup

The protocol-specific ZIP contains this profile and its locked inputs, formal/preflight evidence, replay and smoke results. The framework experience entry is maintained only in the central `基准化经验库.md`, not duplicated inside this ZIP. The ZIP passes archive integrity and per-file source checksum validation; its detached SHA-256 is supplied beside it. After the initial package validation, the dedicated PowerDNS benchmark image and no-longer-needed Ubuntu runtime-base aliases/image were removed; the shared Rocky Linux builder was retained. Exact image/container identities and post-cleanup checks are in `build-logs/image-cleanup.txt`.
