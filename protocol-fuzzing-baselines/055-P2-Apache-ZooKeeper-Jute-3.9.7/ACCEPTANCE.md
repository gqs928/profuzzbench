# Acceptance — Apache ZooKeeper 3.9.7 Jute protocol

**Status: complete.** The target was the official ZooKeeper `3.9.7` linux/amd64 image (`sha256:3b91be30a1e7294956efab116f2189b87ec586b356e81ad4ea6452742323ecb8`). Runtime `zkServer.sh version` asserted 3.9.7. Scope was the standalone unauthenticated plaintext client protocol on TCP/2181; quorum/ZAB, TLS, SASL, and multi-node consensus were excluded.

The formal AFLNet run reached its 30-minute deadline and exited through the recorded SIGINT handler (return code 0). AFLNet recorded 1,802 seconds from `start_time` to its last update, 397 executions, 8 paths, 100.00% stability, 0 crashes, 0 hangs, and `cycles_done=0`. Each testcase reset restarts the ZooKeeper JVM and clears its data directories; observed throughput was about 0.19 exec/s, so the initial queue cycle did not finish. Treat this as a valid time-bounded initial baseline, not a completed-cycle or source-coverage claim. The ZooKeeper JVM was not coverage-instrumented; the helper bitmap is not target-source coverage.

Queue replay covered 19 samples from the raw, replayable, and new-IPSM queues. All 19 reached a ready target, 50 protocol responses were parsed, no replay row had classified errors, and the target stop hook exited 0. A post-run smoke completed 3 valid ZooKeeper client sessions and 27 successful replies. The earlier preflight smoke remains separately preserved under `results/zookeeper-smoke-post-20261112/`.

The package includes the pinned source/image identities, adapter and lifecycle patches, build/runtime evidence, run parameters, raw AFLNet results, replay records, and post-run smoke. Its ZIP and SHA-256 sidecar are verified. Cross-protocol automation lessons are maintained only in the central experience library, not duplicated in this archive.
