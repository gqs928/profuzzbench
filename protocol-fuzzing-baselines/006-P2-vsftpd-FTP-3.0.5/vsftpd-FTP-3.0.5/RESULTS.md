# vsftpd 3.0.5 FTP/TCP baseline results

## Build and service validation

- Source: official `vsftpd-3.0.5.tar.gz`; SHA-256 `26b602ae454b0ba6d99ef44a09b6b9e0dfa7f67228106736df1f278c70bc91d3`. The detached signature verified as a good signature from Chris Evans, key fingerprint `67A2AB4F41F9972C21F6BF667B89011BCAE1CFEA`.
- AFLNet: commit `0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732`; archive SHA-256 `251f24bf2dddb8118eab56ef2b90c92b06f67c096c62543659eaaf31a31d955d`.
- Base: Ubuntu 24.04 digest `sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852`.
- Final image at build time: `vsftpd-ftp-aflnet:3.0.5`, ID `sha256:1293412721debeb766043f3a74ce9abade0cba009a97d53b2ad6e7e74d5a1bdd`.
- Reference and AFL/ASan builds each passed three real FTP control-session smoke runs. Response codes and full transcript hashes matched across variants; transcript SHA-256 `86480e29994de47d2321b97427715b60184ae66dc3d5ea22545cd6c388f638b`.
- AFLNet preflight (30 seconds) completed with 36 executions, 12 paths, and zero unique crashes or hangs.

## Formal campaign

The isolated campaign ran for 1,800 seconds. Both the external timer and AFLNet statistics record the full duration; the timeout wrapper returned 124 after the requested interval.

| Measure | Result |
|---|---:|
| Executions | 1,708 |
| Paths | 98 |
| Variable paths | 0 |
| Stability | 100.00% |
| AFLNet bitmap coverage | 1.74% |
| AFLNet unique crashes | 0 |
| AFLNet unique hangs | 0 |

The measured throughput was about 0.95 executions per second. These numbers describe the single-client FTP control profile and should not be read as file-transfer, TLS, or data-channel coverage.

## Queue replay and source coverage

All 98 queue files were replayed in fresh gcov-target processes. The replayer uses AFLNet's FTP `CRLF` frame boundary and the campaign's 2.5-second response limit. It records complete response text, response codes, target liveness at a timeout, and process exit code.

| Replay outcome | Count |
|---|---:|
| Full response exchange completed | 77 |
| Connection/session closed without a complete exchange | 13 |
| No response within 2.5 seconds; target alive at deadline | 5 |
| Client write failed because the target closed the socket | 3 |

The five silent-session samples were repeated three times each against both the gcov and AFL/ASan variants. All 30 attempts reached the 2.5-second deadline with the server still alive; no ASan diagnostic was observed. AFLNet itself recorded zero unique hangs. These are reproducible session no-response candidates, not a confirmed defect; preserve them for future framework triage rather than dropping them or converting them into confirmed crashes. Per-attempt evidence is under `results/build/hang-candidate-replay/` and `results/build/hang-candidate-afl-replay/`.

Thirteen gcov replays returned process exit code 2. The same samples were checked against AFL/ASan: nine returned code 2, one returned code 1, and three remained alive after their recorded replies until the replay helper's one-second shutdown grace expired (exit -15). No ASan report or `500 OOPS` text appeared. These are retained as nonzero-exit observations, separate from AFLNet's zero signal-crash count, in `results/build/exit2-candidate-afl-replay/`.

The full queue replay produced source coverage of 1,821/6,366 lines (28.6%), 630/3,343 branches (18.8%), and 201/613 functions (32.8%) across upstream C files. This is coverage for the replayed queue under the documented profile, not total vsftpd coverage.

## Scope and limits

The target is vsftpd's FTP control channel over TCP/IPv4 loopback. The container has no external network. Anonymous login is enabled, writes and downloads are disabled, and active/passive data channels are disabled. FTP data transfers, TLS, IPv6, and remote deployment modes are outside this baseline.

The source patch adds a single-client lifecycle for AFL/gcov operation, allows the AFL/ASan build to override upstream's 200 MiB address-space limit, keeps an AFLNet session alive after QUIT until AFLNet stops it, and flushes gcov data by using normal `exit()` in the coverage-only target. Each macro is scoped to its intended build variant. See `source/vsftpd-fuzz-lifecycle.patch`, the build flags in `Dockerfile`, and detailed rows in `results/ftp-30m/coverage/queue-replay.jsonl`.
