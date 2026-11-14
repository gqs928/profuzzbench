# Postfix SMTP baseline

This profile pins official stable Postfix 3.11.7 ([release announcement](https://www.postfix.org/announcements/postfix-3.11.7.html), [signed source archive](https://postfix.cs.utah.edu/source/official/postfix-3.11.7.tar.gz)), verifies its GPG2 signature and SHA-256, and runs the upstream SMTP daemon on loopback TCP port 2525. AFLNet supplies SMTP response-state feedback. GCC gcov counters from Postfix daemon processes are collected and reported separately; AFLNet helper bitmap is not target coverage.

The profile exercises SMTP commands, envelope state, message DATA framing, and server responses. It disables STARTTLS and external relay. The configured discard transport accepts and drops completed local messages so the isolated target cannot deliver mail outside the test.

Build with `./build.sh`, run the 60-second acceptance pass with `./preflight-benchmark.sh 60`, then run `./run-benchmark.sh 1800 postfix-smtp-30m-20261113`. The image runs without network access, with a two-CPU quota and 4 GiB memory limit. The formal campaign completed for exactly 1,800 seconds: 2,877 executions, 8 AFLNet paths, 100% stability, 0 unique crash/hang, and 0.01% helper bitmap. Postfix daemon gcov is reported separately: 14.3% lines, 20.1% functions, and 10.0% branches.

Queue validation decodes raw AFLNet queue files and the `-E` replayable files (u32 little-endian request lengths) separately. In the final 20-case replay, every case received a 220 greeting; 89 requests included 3 DATA transactions, each receiving 354 and the final 250 response; there were 0 timeouts or connection errors, Postfix stayed healthy, and its listener closed after cleanup. See `HARNESS-CORRECTION.md` for the corrected framing and replay evidence.

After candidate ZIP CRC/SHA-256 validation and a zero-container-reference check, the 976,158,928-byte Postfix image was removed by exact ID. Its ID and tag were both confirmed absent; the cleanup record is `build-logs/cleanup.json`. No global image prune was used. Framework guidance is added only to the central aggregated `基准化经验库.md`.
