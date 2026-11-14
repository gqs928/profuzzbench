# UnrealIRCd 6.2.7.1 IRC benchmark results

## Scope and build identity

This profile fuzzes plaintext IRC on loopback TCP/6667 with AFLNet 2.56b and a CRLF-aware IRC adapter. TLS on TCP/6697 is checked by protocol smoke only. WebSocket, IPv6, server links, external DNSBLs, and external IRC services are outside this result. Reference, AFL/ASan, and gcov builds all use the same UnrealIRCd 6.2.7.1 source archive (`4e372ba071f3211d34c5a3515af77fc2b275eb692e43e55c423e201b60958c3f`). AFLNet is pinned to commit `0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732`.

The reference/AFL/gcov smoke matched on parsed IRC numeric-reply sequences for registration, CAP negotiation and JOIN, message/PING, channel modes/WHO, and an unsupported capability request. The smoke client answers server PING challenges, ends CAP negotiation, and waits for numeric 001 before issuing commands that require registration. TLS registration also passed on all three builds. Raw response byte counts are diagnostics; small differences in dynamic response text do not indicate protocol-path differences.

## Formal AFLNet campaign

The detached container ran for 1,800 seconds. `timeout` returned the expected 124 to `run.sh`, and the container exited 0 after writing the result files. `start_time=1794198732` and `last_update=1794200532` differ by exactly 1,800 seconds.

| Metric | Result |
|---|---:|
| Executions | 2,629 |
| Queue paths | 103 |
| `paths_found` | 98 |
| Variable paths | 103 |
| Stability | 90.63% |
| AFL bitmap coverage | 21.24% |
| `cycles_done` | 0 |
| Unique crashes / hangs | 0 / 0 |
| Slowest execution | 1,364 ms |
| IPSM graph | 9 nodes, 34 edges |

The graph passed Graphviz parsing. The campaign did not complete its first queue cycle, and stability is below 95%; treat this as an exploratory baseline, not a stable coverage comparison. `bitmap_cvg` is AFL feedback, not source-line or branch coverage. The short 60-second validation run is retained separately under `validation-final/` and is not substituted for these formal statistics.

## Queue replay and gcov

All 103 queue samples connected to the gcov-enabled target; replay reported 0 errors. The target-source-only report covers 13,227 of 59,749 lines (22.14%) across 309 `src/` files. The full gcovr report is also retained and includes bundled PCRE2 files; the 22.14% figure is computed from UnrealIRCd `src/` rows only. This is independent queue-replay coverage, not campaign bitmap coverage. No branch-coverage figure is claimed.

Evidence is in `irc-30m/campaign/` (`fuzzer_stats`, `ipsm.dot`, `ipsm.plain`, queue, replay classifications and run log) and `irc-30m/coverage-replay/` (`replay.json`, `coverage.txt`, and `gcovr.log`). The completed Docker container's stdout is saved in `irc-30m/run.log`; its exit code was 0. An earlier interactive attempt stopped at 16 minutes and is kept under `results/diagnostics/`, excluded from this report and the independent package.
