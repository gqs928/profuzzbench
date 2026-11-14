# libssh 0.12.2 SSH parser benchmark acceptance

## Identity and scope

- Source: upstream `libssh-0.12.2.tar.xz`, SHA-256 `49560f677d96e3706a904ac2de1116e25f3680937d51e5c92198fcba4a1c1e9f`.
- Detached GPG signature: good signature from key fingerprint `88A228D89B07C2C77D0C780903D5DF8CFDD3E8E7`; transcript and public key are included under `source/` and `build-evidence/`.
- Target: upstream `tests/fuzz/ssh_server_fuzzer`, using a socketpair to drive the SSH server parser/state machine in process. This is not a network server benchmark.
- Backend: one LLVM libFuzzer worker with ASan and UBSan. Upstream fuzz mode enables the `none` cipher/MAC. `WITH_EXEC=OFF` prevents fuzzed channel/configuration input from invoking external commands.
- Seed source: upstream `ssh_server_fuzzer_corpus`; seed and evolved corpora are preserved per run.

## Acceptance results

| Run | Requested | Observed | Executions | cov | features | exec/s | Peak RSS | Exit | Sanitizer findings |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Preflight | 60 s | 62 s outer / 61 s libFuzzer | 50,606 | 3,134 | 8,832 | 829 | 518 MB | 0 | 0 ASan, 0 UBSan |
| Formal | 1,800 s | 1,801 s outer / 1,801 s libFuzzer | 1,242,579 | 3,278 | 10,056 | 689 | 526 MB | 0 | 0 ASan, 0 UBSan |

The formal run began at `2026-11-13T23:04:33Z` and ended at `2026-11-13T23:34:34Z`. Its final corpus contained 1,125 files / 619,002 bytes. No sanitizer artifacts were generated. The raw logs, timestamps, run parameters, final metrics, corpus, and build evidence are included in `results/` and `build-evidence/`.

## Limits

The libFuzzer `cov` value is a coverage-counter count, and `ft` is a libFuzzer feature count. They are not source line coverage. AFLNet stability/bitmap, TCP readiness, listener checks, and network queue replay do not apply to this in-process target.
