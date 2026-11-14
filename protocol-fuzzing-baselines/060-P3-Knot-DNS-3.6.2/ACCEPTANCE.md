# Knot DNS 3.6.2 — acceptance record

Status: complete.

## Version and build

- Upstream Knot DNS 3.6.2 source archive SHA-256: `2916ac117ac77d1f2341a6562e47d797493521b791b414960a382cb5bc113e21`; detached release signature verified with the pinned CZ.NIC signer fingerprint `742FA4E95829B6C5EAC6B85710BB7AF6FEBBD6AB`.
- Runtime base: Ubuntu 24.04 amd64, pinned digest `sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852`.
- Knot DNS and AFLNet compiled successfully. The C DNS/TCP framing parser test passed; the image accepted 64 repeated valid `-N tcp://127.0.0.1/5300` parses, verified AFLNet parser symbols, and passed the dynamic-library check.
- The compiler-wrapper collision was corrected by selecting `/usr/bin/cc -B/usr/bin/` for the standalone parser test. `build-logs/build.log` records the final successful build. Earlier failed build/preflight images were removed by exact image ID and are listed in `build-logs/image-cleanup.txt`.
- Three preliminary preflight attempts exposed unsupported/misplaced Knot configuration items and did not reach fuzzing. The final configuration follows the 3.6.2 sample/schema: `storage` is under `database`; `server.listen` binds the endpoint and the benchmark driver sends DNS/TCP only. Failed attempts remain outside the delivered evidence roots; details are in `build-logs/preflight-config-correction.txt`.

## Preflight and formal campaign

- Successful 20-second preflight: `results/knot-dns-preflight-r4-20261112`. DNS/TCP readiness returned one authoritative answer; deadline was reached through SIGINT and the child exited 0. Stats: 17 executions, 8 paths, 0 crash/hang. Its short duration is a startup/driver check, not a performance estimate.
- Formal AFLNet `-n` response-state run: `results/knot-dns-fuzz-30m-20261112`, planned for 1,800 seconds. `fuzzer_stats` spans 1,797 seconds (`start_time=1794480675`, `last_update=1794482472`). The supervisor reached its deadline, sent SIGINT twice at one-second intervals, and observed child return code 0; `run.sh` normalized the expected deadline exit.
- Final stats: 1,417 executions; 8 paths; 5 completed cycles; 100% stability; 0 variable paths; 0 crash; 0 hang; helper bitmap 0.00%. This is a bounded initial black-box DNS/TCP response-state baseline. The daemon is not AFL-instrumented; the bitmap is not Knot source coverage.
- Each testcase stops and restarts the isolated Knot process, recreates runtime storage, and checks a framed authoritative DNS/TCP query before fuzzing. Throughput therefore includes target restart/readiness overhead. The configured zone file stays immutable.

## Replay, smoke, and cleanup

- Queue replay covers 8 raw queue samples, 8 KL-framed replayable-queue samples, and 2 KL-framed new-state samples: 18/18 passed reset/readiness, each produced one DNS response, and the target remained alive. RCODE counts: 15 NOERROR and 3 NXDOMAIN; zero replay events; replay stopped Knot successfully.
- Post-campaign smoke passed 9 authoritative DNS/TCP queries across three passes (A, AAAA, and negative lookup). The listener-closed check confirmed TCP/5300 refused connections after shutdown.
- After the first ZIP integrity check, removed the exact Knot benchmark and superseded image IDs recorded in `build-logs/image-cleanup.txt`; `docker ps -a` showed no remaining containers. Preserved the shared Ubuntu base for #61 and the shared Rocky builder. No global image or build-cache prune was run.
- The standalone ZIP is `60-Knot-DNS-3.6.2.zip` in the central delivery directory. Its SHA-256 sidecar is generated and verified by `package.py`. Framework experience belongs only in the central `基准化经验库.md`, not this protocol package.
