# Courier POP3 30-minute baseline

Official Courier-IMAP 6.0.7; POP3 plaintext TCP. The run used the shared image recorded in `../../build-logs/image-id.txt`, AFLNet 2.56b, a pinned and manifest-checked corpus, and a deterministic mailbox reset before each testcase.

- Duration: 30m requested; 1,796 seconds in fuzzer_stats; fuzzer_exit_status=124 (expected timeout/SIGINT).
- AFLNet result: 2,345 executions; 70 paths; 55 variable paths; 85.46% stability; 0.78% bitmap; 0 crashes; 0 hangs.
- Protocol smoke evidence is stored next to `fuzzer_stats`; bitmap coverage is AFL feedback and is not source-line or branch coverage.
