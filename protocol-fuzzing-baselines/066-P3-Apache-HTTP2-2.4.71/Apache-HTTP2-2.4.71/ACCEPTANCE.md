# Apache HTTP/2 baseline acceptance

Status: complete

## Target scope

- Apache HTTP Server 2.4.71 from its official signed source archive, with AFL-instrumented `httpd`, `mod_http2`, and the `prefork` MPM.
- Direct cleartext HTTP/2 (`h2c`) over TCP using the HTTP/2 connection preface; one connection per testcase. The corpus includes one-request and two-request-stream transcripts. TLS, HTTP/1.1 Upgrade, proxy modules, and external services are outside this run.
- The server returns a fixed body marker. Strict Python `h2` smoke checks before and after fuzzing each completed three HTTP/2 handshakes, verified status 200, and found the marker in the response body.
- Apache documents that `prefork` processes one request at a time per HTTP/2 connection. This is a bounded direct-h2c protocol-input profile, not a concurrent-stream throughput benchmark. Although `AH10034` appears in the target log, direct h2c was independently verified by successful strict HTTP/2 exchanges.

## Fuzzer adaptation

- AFLNet is pinned to the profile's source snapshot. The HTTP/2 parser patch is applied with zero fuzz; a separate hash-locked lifecycle patch drains 100 ms before server termination, removes AFLNet's busy wait, and retries interrupted `waitpid` calls.
- The custom parser keeps the client preface with a valid initial SETTINGS frame, splits subsequent complete request frames using the 24-bit payload length, and preserves malformed/truncated tails. Response state feedback records complete frame types and flags; it does not decode HPACK status codes.
- AFLNet selects `HTTP2`. The standard AFL forkserver initializes before Apache starts, so each testcase runs a fresh instrumented single-process `httpd -DFOREGROUND -X` child. `-K` sends SIGTERM and the forkserver reaps it. No launcher or skipped instrumentation check is used.
- The 60-second preflight had nonzero AFL bitmap feedback, no crash/hang classifications, completed target executions, and left the listener closed.

## Campaign and delivery

- The formal run reached 1,801 seconds: 5,924 executions, 115 paths, 36.74% stability, 9.81% bitmap, zero unique crashes, and three AFLNet hang classifications. Stability was low and is reported as a limitation. The distribution `libnghttp2` dependency is not AFL-instrumented, so the bitmap is not full Apache source coverage.
- All 115 queued inputs replayed against fresh targets: every target started and remained alive after input, the replay recorded 243 HTTP/2 response frames, and every target exited cleanly after controlled cleanup.
- Each of the three AFLNet hang samples lacked a valid HTTP/2 preface. Replaying them returned an HTTP/1.1 400 response, zero HTTP/2 response frames, left the Apache process alive after input, and produced exit code 0 after controlled SIGTERM. These are malformed-input/no-HTTP2-response classifications, not process hangs.
- The listener was verified closed after fuzzing and after queue replay. The package validator checks source and patch hashes, campaign duration and counters, smoke tests, complete queue/hang replay, listener state, ZIP CRC, and SHA-256.
- The exact Apache benchmark image tags were removed after evidence validation and the cleanup result is included in the ZIP. The central workbook, version checklist, and shared experience library are maintained separately; the experience library is not included in this protocol ZIP.
