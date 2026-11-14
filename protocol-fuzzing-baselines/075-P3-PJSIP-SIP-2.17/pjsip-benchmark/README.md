# PJSIP SIP parser native fuzz baseline

This profile benchmarks the upstream PJSIP 2.17 `tests/fuzz/fuzz-sip.c` harness with LLVM libFuzzer and AddressSanitizer. It exercises SIP parsing and selected transaction/authentication/dialog paths in process; it does not start a SIP server or measure network-state responses.

Build with `./build.sh`, run the 60-second preflight with `./preflight-benchmark.sh`, then run the formal campaign with `./run-benchmark.sh 1800 pjsip-fuzz-30m-20261113`. The official PJSIP seed corpus is copied into each run output so generated corpus is preserved with the evidence. Native libFuzzer metrics are used; AFLNet stability, bitmap, readiness, and network replay fields are not applicable. The framework experience is centralized and excluded from this individual ZIP.

The 60-second preflight passed with 661,112 executions. The formal libFuzzer run completed 1,865 seconds against a requested 1,800 seconds, reaching 7,840,988 executions, 1,519 covered edges, and 6,843 features with no sanitizer or crash markers. The final image passed a 10-second smoke with the corrected metrics summary: 115,149 executions and 1,385 covered edges. See `ACCEPTANCE.md` for corpus growth, peak RSS, and the outer wall-clock span.
