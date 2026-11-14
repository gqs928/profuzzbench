# Acceptance — Unbound DNS/TCP baseline

Status: complete.

## Locked target

- Product/version: Unbound 1.26.2, official release dated 2026-10-21.
- Source: `source/unbound-1.26.2.tar.gz`; official SHA-256 `d8ee7aa6bbb3ff1be7d9e57637d0d0ec2f18273a8efff1a0afe2c665858b96f7`; release signature validated by NLnet Labs releases G2 fingerprint `231018690C4D903EF419146AA144323DEAACDF45`.
- Scope: DNS/TCP to the local `fuzz.test` static zone on TCP/5300; UDP listener is present but not exercised.
- Feedback: AFLNet black-box DNS response-state feedback; AFL helper bitmap is not target-source coverage.

## Required checks

The final package will record the source-signature/build checks, 20-second functional preflight, 1,800-second formal campaign, per-sample queue replay, three-pass A/AAAA/MX/NXDOMAIN smoke, listener closure, archive integrity and SHA-256, and exact Docker image cleanup.

## Results

- Official archive SHA-256 and NLnet Labs G2 signature passed; build/runtime version assertions confirmed Unbound 1.26.2; `unbound-checkconf` and dynamic-library checks passed.
- The 20-second preflight completed with 20 executions and 8 response-state paths; all 12 preliminary A/AAAA/MX/NXDOMAIN DNS/TCP queries passed.
- The formal 1,800-second deadline was reached and stopped by one SIGINT. AFLNet exited cleanly with return code 0. Reported campaign span was 1,797 seconds, 1,733 executions (1.08 exec/s), 8 response-state paths, 5 cycles, 100% stability, 0 unique crashes, and 0 unique hangs. `bitmap_cvg=0%` is the helper bitmap only; Unbound source coverage was not measured.
- AFLNet printed `WARNING: error waitpid` while handling the deadline SIGINT, then saved the final statistics and exited. The bounded run's return code, complete stats, post-run tests, and listener cleanup all passed; this termination warning is retained as a framework observation.
- All 18 raw/KL queue samples passed per-sample target readiness and replay, produced 18 DNS responses (15 NOERROR and 3 NXDOMAIN), and had 0 replay events; the replay target stopped with exit code 0.
- The post-run three-pass smoke passed all 12 A/AAAA/MX/NXDOMAIN queries, and a same-container check confirmed TCP/5300 was closed after stopping Unbound.
- The protocol delivery ZIP passed internal CRC verification and its SHA-256 sidecar was generated and independently checked. The ZIP contains this target's source, harness, campaign/replay/post-smoke evidence, and acceptance report; the shared experience library remains outside it.
- Removed the completed `unbound-dns-aflnet-bench:1.26.2` image (`sha256:95d4b27116b9f4aa615f7a9f9fb6e4b39e416d633a628de4500fde209591fa77`, 174,451,631 bytes) and the `unbound-runtime-base:24.04` alias. The pinned Ubuntu 24.04 digest image remains available for the three upcoming DTLS builds; no Unbound container or benchmark image tag remains.
