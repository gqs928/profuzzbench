# pynetdicom 3.0.4 — acceptance record

Status: complete. Campaign, queue replay, post-campaign protocol checks, standalone packaging, and exact image cleanup all passed.

## Target and build

The target is the latest stable pynetdicom release verified on 2026-11-12: pynetdicom 3.0.4 with pydicom 3.0.2. The official PyPI wheel SHA-256 values are pinned in `source-lock.json` and `requirements.lock`; the image asserts both installed package versions. The amd64 Python 3.12.16 slim Bookworm runtime is pinned by digest. AFLNet is locked to ProFuzzBench snapshot commit `0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732`.

The DICOM response parser unit passed for multi-PDU framing, C-ECHO command state, association reject detail, and malformed lengths. Build-time linker checks found no unresolved AFLNet dependencies. A generic AFLNet `-N` endpoint terminator patch was applied with zero fuzz; a build gate parsed the same DICOM endpoint successfully 64 consecutive times. The target runtime log level is `warn`, and AFLNet's no-forkserver target stub is the verified `/usr/local/bin/python3` executable.

Two early short-run attempts stopped before a valid multi-sample campaign: `storescp` rejected the unsupported `warning` log-level spelling, the AFLNet endpoint parser exposed its unterminated copy, and a subsequent AFLNet dry-run rejected the wrong Python executable path. These findings were corrected in the profile. The failed output directories are excluded from the delivery; only the successful preflight and formal run are accepted evidence.

## Preflight and formal campaign

The corrected 20-second preflight in `results/pynetdicom-preflight-r2-20261112` completed with 15 executions, 5 paths, no crash/hang, and a successful supervisor record: deadline reached, one SIGINT, AFLNet return code 0.

The formal AFLNet `-n` campaign used the configured 1,800-second deadline. `fuzzer_stats` spans 2026-11-12 10:03:02–10:32:58 UTC (1,796 seconds); the deadline supervisor recorded the deadline, one SIGINT, and child return code 0. The outer wrapper's deadline status 124 is normalized by `run.sh` after AFLNet writes final statistics. AFLNet logged `error waitpid` during interruption, but final statistics and queue data were written. Final stats: 1,228 executions, 5 paths, 2 completed cycles, 100.00% stability, 0 unique crashes, and 0 unique hangs. `bitmap_cvg=0.00%` is the AFLNet helper bitmap and is not pynetdicom source coverage; the Python target was not coverage-instrumented.

## Queue replay and post-campaign health

All 5 raw queue samples were replayed against an independently restarted `storescp`. All 5 passed protocol readiness; there were 0 server-start failures and 0 connection errors. The valid C-ECHO and C-STORE samples each produced one 10-byte P-DATA-TF response; malformed and truncated inputs produced no response. The server remained alive after all 5 samples, with no timeout after a response.

Three post-campaign smoke flows each completed A-ASSOCIATE, C-ECHO status 0, C-STORE status 0, and release. After shutdown, TCP/11112 refused connections. Full logs and machine-readable evidence are under `results/`.

The standalone archive was rebuilt and its ZIP integrity, source checksums, required evidence manifest, and sidecar SHA-256 were verified after cleanup. Exact image IDs and tag/digest aliases removed, plus post-cleanup inventory, are recorded in `build-logs/image-cleanup.txt`. Framework-facing lessons stay only in the central `基准化经验库.md`; this protocol ZIP does not contain that library.
