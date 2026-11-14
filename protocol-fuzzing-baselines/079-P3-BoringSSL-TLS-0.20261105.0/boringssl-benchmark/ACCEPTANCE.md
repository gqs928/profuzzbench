# BoringSSL TLS server fuzzer acceptance

## Identity and scope

- Latest upstream release at version verification: `0.20261105.0` (GitHub release page marked it Latest).
- Tag object: `5e7f7792f2223216967aa9abc6be8e5b1727e41d`; peeled source commit: `3dc4b63808921e914a3fb1fa61869abc3938781b`.
- Source snapshot: git archive of the exact release tag, SHA-256 `87345c7dc8530f2135bea2e60b11f447474d36668e019b0cef4c57693c063422`.
- Target: upstream `fuzz/server.cc` built as `fuzz/server`, using the matching `fuzz/server_corpus`.
- Backend: single-worker LLVM libFuzzer with the upstream `FUZZ=1` instrumentation and AddressSanitizer. The upstream docs recommend `max_len=4096` for this target; this campaign used that value.
- Scope: in-process TLS server handshake/state-machine parsing. No TCP listener is started.

## Acceptance results

| Run | Requested | Observed | Executions | cov | features | exec/s | Peak RSS | Exit | ASan findings |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Preflight | 60 s | 61 s outer / 61 s libFuzzer | 154,093 | 9,568 | 31,161 | 2,526 | 468 MB | 0 | 0 |
| Formal | 1,800 s | 1,807 s outer / 1,805 s libFuzzer | 4,110,930 | 9,859 | 34,011 | 2,277 | 484 MB | 0 | 0 |

The formal run began at `2026-11-13T23:40:02Z` and ended at `2026-11-14T00:10:09Z`. The final corpus contained 4,014 files / 3,840,352 bytes. No sanitizer artifacts were generated. Raw logs, timestamps, run parameters, metrics, corpus, source provenance, and build lock are included.

## Limits

BoringSSL upstream documents `FUZZ=1` as unsafe for production and says it relaxes cryptographic invariants to let TLS parsers/state machines progress. Therefore these counters describe the upstream fuzz-mode target, not a production TLS server or full cryptographic validation. The `cov` value is a libFuzzer coverage-counter count, not source line coverage. AFLNet stability/bitmap, TCP readiness, listener checks, and network queue replay do not apply.
