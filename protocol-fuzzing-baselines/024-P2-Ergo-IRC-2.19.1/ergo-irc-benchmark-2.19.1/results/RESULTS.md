# Ergo 2.19.1 IRC baseline result

## Target and feedback

- Target: Ergo 2.19.1, plaintext IRC over loopback IPv4 TCP/6667. TLS, WebSocket, IPv6, external services, and non-IRC protocols are outside this profile.
- AFLNet: pinned 2.56b (`0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732`) in dumb (`-n`) mode. Feedback is IRC response-state novelty; the target has no AFL code bitmap. `bitmap_cvg=0.00%` is expected and is not a source-coverage result.
- The Go coverage build is a separate replay target. QEMU 2.10.0 cannot run the pinned Go 1.27.3 binary because Go fails to reserve page-summary memory under QEMU, so this baseline does not claim QEMU-derived edge coverage.
- `ergo-target.sh` gives each AFLNet sample a fresh working directory for the relative `ircd.db` and lock file. AFLNet keeps its own state in a separate working directory.

## Formal campaign

The timed command ran for 1,801 seconds; exit status 124 is the expected `timeout` stop signal.

| Metric | Result |
|---|---:|
| Executions | 1,393 |
| Queue paths | 61 |
| New response-state queue items (`+state`) | 56 |
| IPSM graph | 35 nodes, 81 edges |
| `cycles_done` | 0 |
| Stability | 100.00% |
| AFL bitmap coverage | 0.00% |
| Unique crashes / hangs | 0 / 0 |

The first queue cycle was incomplete, so this is a time-limited baseline. The 100% stability value describes AFLNet's observed path stability; it does not mean the initial queue was fully explored.

At shutdown AFLNet printed `error waitpid`. In the pinned AFLNet stop routine this warning is emitted while waiting for the forkserver PID even though dumb mode has no forkserver. It occurred at timeout shutdown; the full 1,801-second `fuzzer_stats`, 124 timeout exit, queue, and graph were all written.

Raw campaign evidence is in `irc-30m/campaign/`, with the host-side command log at `irc-30m/run.log`.

## Go coverage replay

All 61 queue files connected to a fresh Go coverage build instance, with 0 replay errors. The replay report is `irc-30m/coverage/replay.json`; Go's `go tool covdata` / `go tool cover` report 17.4% statement coverage. These statements were collected by replay and are separate from AFLNet's response-state queue feedback. Raw `GOCOVERDIR` counters are in `go-cover-data/`.

## Validation and diagnostics

`validation-final/` contains the successful protocol smoke, 180-second response-state validation, queue replay, and build versions. `diagnostics/` retains two superseded runs with notes explaining why they were excluded from the formal result: one reused Ergo's persistent database across samples and one predated the AFLNet state-only queue patch.
