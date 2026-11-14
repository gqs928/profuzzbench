# Acceptance record

Status: complete.

- Protocol implementation: quic-go v0.65.0, official tag commit `aa265c3fc6489e3bfa8071b333be95e0e887a51d`.
- Target: upstream `internal/wire.FuzzHeaderParser` in `internal/wire/header_test.go`.
- Scope: QUIC v1/v2 long and short header parsing, connection-ID lengths, packet types, and Version Negotiation parsing. This is an in-process parser target; it does not start a UDP service, complete a handshake, or exercise HTTP/3.
- Fuzz engine: Go testing native fuzz backend, Go 1.27.4, two workers, isolated per-run cache.
- Preflight: Go fuzz elapsed 60.092 seconds, 2,253,899 executions; `PASS`, package result `ok`, exit status 0.
- Formal: Go fuzz elapsed 1,800.015 seconds, 63,490,835 executions; 51 new interesting inputs (68 total); `PASS`, package result `ok`, exit status 0. No `FAIL`, panic, or fatal runtime markers were recorded.
- Campaign wall-clock span: 1,819 seconds; see `results/quic-go-fuzz-30m-20261113/run-times.txt`.

Go native fuzz output has no AFLNet stability or bitmap fields. Do not synthesize those metrics or server readiness/listener/replay evidence for this in-process target. The formal and preflight logs, metrics, and generated fuzz corpus are included in this standalone package. Candidate ZIP passed CRC/SHA-256 validation before cleanup. The exact target image ID and tag were removed after confirming zero container references; post-cleanup inspection confirmed the ID/tag and references are absent. Shared base images and build cache were retained. Append implementation-specific framework guidance to the central experience library, not this ZIP.
