# POP3 3.12.4 30-minute baseline

Upstream release: 3.12.4 ([official source](https://www.cyrusimap.org/3.12/imap/download/release-notes/3.12/x/3.12.4.html)).

- Duration requested: 30m. Actual runtime and container exit status are in `run-parameters.txt`.
- AFLNet version: 2.56b; executions: 2376; paths: 102; variable paths: 102; cycles completed: 0; new paths: 97.
- Stability: 93.63%; AFL bitmap: 7.89%; unique crashes: 0; unique hangs: 0.
- Stability is below the 95% profile threshold; treat this run as exploratory, not as a stable coverage-comparison sample.
- AFLNet stopped during its first cycle at the time limit; the queue was not fully explored in this run.
- Bitmap coverage is AFL feedback; this run does not claim source-line or branch coverage.
- The validated short-run protocol smoke and forkserver evidence are under `../pop3-validation/`.
