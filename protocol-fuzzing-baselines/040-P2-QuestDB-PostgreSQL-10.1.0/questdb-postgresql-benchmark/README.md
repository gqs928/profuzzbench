# QuestDB PostgreSQL-wire protocol benchmark

This profile targets QuestDB's PostgreSQL Wire Protocol (PGWire) endpoint on TCP/8812. The implementation is pinned to the official latest stable QuestDB 10.1.0 release checked on 2026-11-10. The benchmark uses the built-in admin credentials only inside an isolated local container and sends bounded, read-only SQL queries.

The AFLNet parser uses PostgreSQL v3.0 StartupMessage and backend framing. The test corpus includes QuestDB's plain password challenge response after StartupMessage. The official QuestDB image is not compiler-instrumented; AFLNet therefore uses network-only state feedback (`-n -E`), and `bitmap_cvg` is not source-code coverage.

## Build and run

```sh
./build-aflnet.sh
./start-server.sh
python3 protocol_smoke.py
./fuzz.sh results/questdb-pgwire-30m 1800
python3 replay_queue.py results/questdb-pgwire-30m
python3 protocol_smoke.py
```

After verifying the independent ZIP and SHA-256, remove the dedicated container and image with `./stop-server-and-remove-image.sh`. The shared framework experience library is maintained outside this package.

## Formal result

See `ACCEPTANCE.md` and `results/questdb-pgwire-30m/` for the 1,800-second run, final response-state totals, 37-case queue replay, and post-run SQL verification. The replayer's bounded idle-read timeout count is reported separately and is not treated as a target hang.
