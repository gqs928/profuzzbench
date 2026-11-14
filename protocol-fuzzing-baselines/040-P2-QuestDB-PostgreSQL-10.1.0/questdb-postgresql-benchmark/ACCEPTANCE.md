# QuestDB 10.1.0 PGWire acceptance record

- Target image: `questdb/questdb:10.1.0`, OCI digest `sha256:3b11dc5f77aa299c7c9191b10cf50124c9e97663ce93bc50df5040374e87efc9`; runtime version probe reported QuestDB 10.1.0.
- Preflight: 61 active seconds; 288 executions, 11 paths, 100% stability, 0 crashes, 0 hangs. Preflight queue replay: 11/11 connected, 93 backend frames, 0 reset/error.
- Formal AFLNet run: **1,800 active seconds**, exit status 0. Final stats: 2,367 executions, 38 total response-state paths (29 discovered), 100% stability, 0 crash candidates, 0 hang candidates, `cycles_done=0`.
- Fuzzer mode: network-only PostgreSQL response-state feedback (`-n -E`), no QuestDB source instrumentation. `bitmap_cvg=0%` is not source coverage.
- Post-run `admin/quest` PGWire smoke: `SELECT 1` returned one row, no error, `CommandComplete`, and `ReadyForQuery`.
- Formal queue replay: 37/37 connected, 353 backend frames, 35 `ReadyForQuery`, 1 SQL error response (the intentional syntax-error seed), 0 resets/network errors, 0 empty responses. The 35 bounded read timeouts mark the idle gap while waiting for additional response frames and can overlap with valid replies; they are not target hangs.
- The seed manifest lives beside `seeds/`, not inside the AFLNet corpus, so all initial corpus entries are protocol messages.

After the delivery ZIP and its internal/external SHA-256 checks were verified, the profile's exact QuestDB container and official image tag were removed to release disk space.
