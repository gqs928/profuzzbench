# Acceptance record

Status: benchmark and target acceptance passed; final package and image cleanup completed.

- Implementation: official Postfix 3.11.7 source archive; SHA-256 and detached GPG2 signature are verified in the image build.
- Target: Postfix SMTP server launched by the upstream master service on loopback TCP port 2525.
- Scope: SMTP commands, envelope transitions, DATA framing, and response states. STARTTLS and external relay are disabled; the configured discard transport accepts and drops completed messages.
- Engine: AFLNet built from the pinned source commit, SMTP response-state feedback, one campaign worker. AFL bitmap values describe only the helper.
- Target coverage: GCC gcov counters from Postfix daemon processes, summarized separately from AFLNet feedback.
- Preflight: passed; preflight and post-smoke transcripts both completed the SMTP envelope, `DATA` 354/body/final 250 exchange, and `QUIT`. Campaign, verified replay, and post-smoke each ended with `shutdown=stopped`, exit code 0, and no listener.
- Formal run: 2026-11-13 22:17:17Z–22:47:17Z (1,800 seconds), AFLNet exit 0; wrapper exit 124 is the expected duration-timer path. Statistics: 2,877 executions, 8 paths, 0 paths found, 0 variable paths, 100.00% stability, 0.01% AFLNet helper bitmap, 0 unique crashes, 0 unique hangs, 4 replayable new IPSM paths. Target GCOV: 14.3% lines (7,703/53,803), 20.1% functions (547/2,720), 10.0% branches (3,791/37,972).
- Verified queue replay: 20/20 inputs connected and received a 220 greeting, comprising 8 raw inputs and 12 AFLNet u32-LE length-prefixed request sequences. All 89 requests completed without timeout; all 3 DATA transactions received 354 and final 250 replies. Postfix master remained healthy (status exit 0). Replay-phase GCOV: 5.9% lines, 10.1% functions, 3.9% branches; this includes readiness plus replay. The initial framing-misread report is retained as an audit file and superseded by the verified `queue-replay.json`.
- Delivery: candidate ZIP passed CRC and SHA-256 validation before cleanup; final ZIP is CRC-tested and accompanied by a SHA-256 sidecar. The exact 976,158,928-byte dedicated image had zero container references, was removed by image ID with `--no-prune`, and both image ID and tag were confirmed absent; see `build-logs/cleanup.json`.

Framework experience is maintained only in the central aggregated experience library. This package contains no per-protocol experience entry.
