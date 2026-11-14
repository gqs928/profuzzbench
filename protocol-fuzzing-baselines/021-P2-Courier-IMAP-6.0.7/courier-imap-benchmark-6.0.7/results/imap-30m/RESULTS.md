# Courier IMAP 30-minute baseline

Official Courier-IMAP 6.0.7; IMAP plaintext TCP. The run used the shared image recorded in `../../build-logs/image-id.txt`, AFLNet 2.56b, a pinned and manifest-checked corpus, and a deterministic mailbox reset before each testcase.

- Duration: 30m requested; container ran 30m06s; fuzzer_exit_status=124 (expected timeout/SIGINT).
- AFLNet result: 2,843 executions; 119 paths; 82 variable paths; 95.07% stability; 1.46% bitmap; 0 crashes; 0 hangs.
- Protocol smoke evidence is stored next to `fuzzer_stats`; bitmap coverage is AFL feedback and is not source-line or branch coverage.
