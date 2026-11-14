# FRRouting 10.7.1 — acceptance record

Status: complete. The protocol-specific ZIP and SHA-256 sidecar are validated; experience stays in the central experience library.

- Release/image: FRRouting 10.7.1; official linux/amd64 image digest is pinned in `source-lock.json`; `bgpd --version` returned `10.7.1_git`.
- Parser and smoke: BGP framing/parser unit passed; three pre-campaign smoke passes exercised OPEN/KEEPALIVE/UPDATE and verified listener closure. A 20-second preflight completed 19 executions, six paths, 100% stability, and no crash/hang.
- Formal campaign: requested 30 minutes; `fuzzer_stats` spans 1,798 seconds and the deadline record confirms SIGINT shutdown with AFLNet exit code 0. Final stats: 2,010 executions, 1.07 exec/s, 12 cycles, 6 paths, 100% stability, 0.00% helper bitmap, 0 unique crashes, 0 unique hangs. The bitmap is not FRR source coverage; the small queue and low throughput are a bounded initial baseline, not a coverage claim.
- Replay: 14 samples across raw queue, KL-framed replayable queue, and newly discovered IPSM paths; 14/14 reset/readiness checks passed, with 30 BGP response messages. Eight malformed/short samples ended by peer close; the target process remained controlled and stopped with code 0.
- Post-run: three independent OPEN/KEEPALIVE/UPDATE smoke passes succeeded; the BGP listener was closed after target shutdown.
- Packaging: `57-FRRouting-BGP-10.7.1.zip` includes only this protocol's implementation and formal/post-smoke evidence. The central automation experience library is not embedded.
- Docker cleanup: after package verification, remove the exact FRR target/runtime tags and benchmark image; keep the shared Rocky build image for later profiles.
