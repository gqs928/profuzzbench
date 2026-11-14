# Acceptance record: RabbitMQ STOMP 4.4.0

Version selection: RabbitMQ Server 4.4.0, the latest upstream stable release checked on 2026-11-09; the official release is marked `Latest`. The generic Unix distribution signature and SHA-256 were verified before build. `source-lock.json` records the release archive, signing-key fingerprint, Erlang base-image digest, and AFLNet commit.

The target identified itself as RabbitMQ 4.4.0 on Erlang/OTP 29.0.6. Before formal fuzzing, STOMP 1.2 negotiation, subscription receipt, and message delivery passed after aligning the `host:/` header with RabbitMQ's default `/` virtual host. The 26-second preflight completed with 80 executions, eight paths, 100% stability, and no crash or hang.

The formal campaign exited with status 0 after 1,801 active seconds. AFLNet recorded 2,472 executions, 100 total paths, 95 newly found paths, zero variable paths, 100% stability, 0.00% bitmap coverage, zero unique crashes, zero unique hangs, and `cycles_done=0`. This is black-box STOMP response-state feedback; the bitmap is not RabbitMQ Erlang source coverage.

Post-run replay connected to all 100 queue samples: 99 produced a recognized NUL-terminated STOMP frame, one closed without a recognized response, and there were zero timeouts, resets, or replay errors. A fresh STOMP smoke passed both before and after queue replay, confirming the broker remained healthy. Replay counts are in `results/replay-summary.json`.

The standalone package ZIP and SHA-256 sidecar were checked before deleting the exact `rabbitmq-stomp-440` container and `profuzzbench-rabbitmq-stomp:4.4.0` image.
