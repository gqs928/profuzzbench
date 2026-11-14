# Acceptance record

Status: accepted; formal campaign, package CRC/SHA validation, and exact image cleanup passed.

- Implementation: Fortra Impacket 0.13.1, pinned to the official release and PyPI source archive SHA-256.
- Target: in-process SMB2/SMB3 wire-structure parsing in upstream `impacket.smb3structs`.
- Scope: bare and RFC 1002-framed SMB2/3 messages, selected command bodies and variable-length contexts, compound messages, encrypted/compressed transform headers. No SMB1, listener, authentication exchange, remote server, or network replay.
- Engine: Atheris 3.1.0 / LLVM libFuzzer with Python bytecode instrumentation; one worker.
- Seeds: deterministic SMB2/3 request/response corpus generated from Impacket's upstream structure classes.
- Preflight: passed 2026-11-13 UTC; 61 engine seconds, 41,453 executions, 186 new units, 184 Python coverage edges, 883 features, 50 MB peak RSS, exit code 0, no failure markers.
- Formal: 1,801 engine seconds (outer interval `2026-11-13T21:11:00Z`–`2026-11-13T21:41:01Z`), 555,056 executions, 304 new units, 184 Python coverage edges, 1,071 features, 50 MB peak RSS, 153 saved corpus files, exit code 0, and an empty `failure_markers` list. Raw output and machine-readable metrics are in `results/impacket-smb-30m-20261113/`.
- The raw log contains three libFuzzer startup warnings about optional `__sanitizer_*` callback symbols being unavailable. They are preserved as runtime compatibility warnings; there is no sanitizer error, uncaught exception, or libFuzzer failure marker, and this profile does not claim ASan instrumentation.
- Candidate package `76-Impacket-SMB-0.13.1-candidate.zip` passed ZIP CRC validation and SHA-256 `2d299652f6b67b74bbc55cf4bf64a3f472bb8fcf73e90c73901108b076964364` before cleanup. With no containers referencing it, the 319,371,732-byte image ID `sha256:cfda4d637fc2e63cc28e343bcf564b3814400159e6b29af436bb7a74b6c86a7a` was removed with `docker image rm --no-prune`; both ID and tag were confirmed absent. Evidence: `build-logs/cleanup.json`.
- Final standalone ZIP CRC passed after adding the cleanup evidence; its sidecar SHA-256 is stored alongside the central delivery package.

Report Atheris/libFuzzer execution, elapsed time, Python coverage edges/features, corpus growth, exit code, and failure markers. AFLNet stability/bitmap, server readiness/listener, and network replay metrics do not apply. The 30-minute campaign passed without uncaught Python exceptions or libFuzzer failure markers, and saved logs/metrics/corpus. Candidate ZIP CRC/SHA-256 validation and exact image cleanup after confirming no container references are recorded in `build-logs/cleanup.json`. Framework guidance belongs only in the central aggregated experience library.
