# POP3 2.4.5 30-minute baseline

Upstream release: 2.4.5 ([official source](https://dovecot.org/releases/2.4/)).

- Duration requested: 30m. Actual runtime and container exit status are in `run-parameters.txt`.
- AFLNet version: 2.56b; executions: 1791; paths: 38; variable paths: 38; cycles completed: 0; new paths: 33.
- Stability: 86.68%; AFL bitmap: 16.33%; unique crashes: 0; unique hangs: 0.
- Stability is below the 95% profile threshold; treat this run as exploratory, not as a stable coverage-comparison sample.
- AFLNet stopped during its first cycle at the time limit; the queue was not fully explored in this run.
- Bitmap coverage is AFL feedback; this run does not claim source-line or branch coverage.
- The validated short-run protocol smoke and forkserver evidence are under `../pop3-validation/`.
