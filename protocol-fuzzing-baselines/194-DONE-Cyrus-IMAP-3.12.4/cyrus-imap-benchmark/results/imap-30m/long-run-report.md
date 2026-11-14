# Cyrus IMAP 30-minute fuzz run — supplemental report

This report supplements the earlier complete acceptance report. New run artifacts are isolated under `results/imap-30m/` and `results/imap-30m-coverage/`; earlier result directories were not modified.

## Target and duration

- Target: hash-pinned Cyrus IMAP 3.12.4 / AFLNet 2.56b image `cyrus-imap-fuzz` (`sha256:01ba131e1dcf6ea0048f6338f92d980dcad4a30cd5c53e3ffbbce0d8f81b9da0`). The image was present before the run; package source/archive SHA-256 checks passed.
- Command: `bash /workspace/run.sh /results/imap-30m 30m`, with the README Docker isolation and mounts.
- Host wall time: **1801 seconds** from `2026-10-01T03:30:24-04:00` to `2026-10-01T04:00:25-04:00`.
- AFLNet 2.56b's native `fuzzer_stats` has no `run_time` key. The recorded `start_time` and `last_update` differ by **1800 seconds**, verifying the requested 1,800-second fuzz window. See the unmodified `fuzzer_stats` and `runtime-verification.txt`.

## Fuzzer result

- Executions: 1541; paths: 76; variable paths: 76.
- Stability: 92.99%; bitmap coverage: 17.02%.
- Queue: 76 inputs; replayable queue: 76 inputs.
- IPSM: 16 states and 39 transitions in `ipsm.dot`.
- `cycles_done=0` at timeout, so AFLNet had not completed one full corpus cycle when the 30-minute limit was reached.
- Unique crashes: **0**; unique hangs: **0**. Both replayable anomaly directories are empty, so there were no Cyrus crash/hang samples to reproduce. The separate fault-probe fixture is not counted as a Cyrus finding.

## Coverage replay

`coverage-run.sh` replayed all **76/76** queue inputs (`QUEUE_LIMIT=0`) on reset instances of the clean gcov-instrumented Cyrus server; replay errors: 0.

- Lines: 13102/76797 (17.1%).
- Branches: 6245/52479 (11.9%).
- Fresh gcov files: 139; `imapd.gcda`: 59312 bytes.
- Generated detailed HTML reports: 188.

## Evidence

- Fuzz queue, native `fuzzer_stats`, `plot_data`, `ipsm.dot`, `run.log`, replayable inputs, `runtime-verification.*`, and `SHA256SUMS` are in this directory.
- Coverage replay logs, HTML, summary, `coverage-provenance.txt`, and `SHA256SUMS` are in `results/imap-30m-coverage/`.
- `runtime-verification.json` contains machine-readable timing and summary values.
