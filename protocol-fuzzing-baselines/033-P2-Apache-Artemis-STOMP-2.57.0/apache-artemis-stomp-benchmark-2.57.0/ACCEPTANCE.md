# Acceptance record: Apache ActiveMQ Artemis STOMP 2.57.0

Version selection: 2.57.0, the latest upstream stable release checked 2026-11-09. The official Apache distribution checksum passed before the image build; the profile pins the distribution, JRE, AFLNet source, and base image in `source-lock.json`.

The new-instance STOMP 1.2 smoke passed before and after the formal campaign. It verified CONNECTED negotiation, SUBSCRIBE receipt, and message delivery. The 26-second preflight completed with 73 executions, six paths, 100% stability, and no AFLNet crash or hang.

The formal campaign ended with exit status 0 after 1,802 active seconds. AFLNet recorded 2,489 executions, 64 total queue paths, 59 newly found paths, zero variable paths, 100% stability, 0.00% bitmap coverage, zero unique crashes, zero unique hangs, and `cycles_done=0`. This profile is Java binary black-box state feedback; the zero bitmap is not a Java source coverage result.

Queue replay ran inside the target container: 64 samples, 62 with a recognized STOMP response, two without a recognized response, and zero replay errors. The two silent samples are retained as queue inputs; the post-run smoke confirmed the broker remained healthy. Replay counts are recorded in `results/replay-summary.json`.

The independent ZIP and SHA-256 sidecar are verified in the parent delivery directory. After verification, the exact `artemis-stomp-2570` container and `profuzzbench-artemis-stomp:2.57.0` image were removed to reclaim space.
