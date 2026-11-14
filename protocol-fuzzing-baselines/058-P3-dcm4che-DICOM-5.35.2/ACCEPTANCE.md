# Acceptance — dcm4che 5.35.2 DICOM UL/TCP

Status: complete for the official full-toolkit `storescp` target. As of 2026-11-12, 5.35.2 is the latest complete dcm4che3 binary distribution containing `storescp`; the separate `dcm4che-core` Maven index lists 5.36.0, but that module is not a newer complete SCP toolkit. `storescp -V` in the built image asserted 5.35.2. The official archive SHA-256 is `fbb9ec00858d61f6e9f0e05990d544a0a9a92f3ddacdc59cf66e188f9a0617a8`.

The DICOM parser unit test passed. A 20-second preflight reached the target, processed 11 inputs across 5 paths, and recorded 0 crash/0 hang; it is harness evidence only, not a stable fuzz result. The pre- and post-build DICOM smoke tests completed A-ASSOCIATE, C-ECHO, C-STORE, and release; the post-campaign smoke passed all 3 flows with C-ECHO/C-STORE status 0.

The formal AFLNet run used the configured 1,800-second deadline. AFLNet `start_time` was 2026-11-12 09:20:00 UTC and its last recorded update was 09:49:59 UTC; the deadline supervisor then sent one SIGINT. The supervisor recorded `deadline_reached: true` and child return code 0. Its expected outer timeout status was 124. AFLNet logged `error waitpid` during interruption, but wrote final stats and the target stopped cleanly. Final stats: 1,014 executions, 5 total paths, 100.00% stability, 0 unique crashes, 0 unique hangs, 1 completed cycle, and 0.00% AFL helper bitmap. The bitmap is not dcm4che source coverage; the Java target was not instrumented.

Queue replay selected and replayed 5/5 samples in independent fresh `storescp` processes. All 5 servers passed readiness, with 0 connection errors; 3 samples produced 7 response PDUs (864 bytes total), and the malformed/truncated samples received no PDU response. The server process remained alive after all 5 inputs, with no replay timeout after response. The three post-run smoke passes each completed association, C-ECHO, C-STORE, and release successfully. After shutdown, the TCP listener refused connections on port 11112.

Formal stats, deadline record, run parameters, replay records, post-smoke transcript, listener check, version/build evidence, and source checksums are included in the protocol ZIP. Framework-facing lessons are maintained only in the central `基准化经验库.md`.

After the initial ZIP/SHA-256 validation, the dcm4che benchmark image and its pinned Eclipse Temurin target base were removed by exact image ID (591,099,978 and 286,902,214 bytes). No containers remain; the shared Rocky builder was retained for subsequent protocols. The cleanup record is in `build-logs/image-cleanup.txt`.
