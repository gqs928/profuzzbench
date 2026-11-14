# ScyllaDB 2026.3.5 — Native Protocol benchmark

This profile benchmarks unauthenticated ScyllaDB Native Protocol v4 over TCP port 9042. It uses the official ScyllaDB 2026.3.5 linux/amd64 image pinned by manifest digest. ScyllaDB's product binary reports 2026.3.5-0.20261103.76a3b0773cfe. The CQL field system.local.release_version reports 3.0.8, a protocol compatibility value rather than the product release number.

The official release announcement for ScyllaDB 2026.3.5 is at https://forum.scylladb.com/t/release-scylladb-2026-3-5/5575. The image identity and digest are in images.env and source-lock.json.

## Build and run

The build script uses the pinned ScyllaDB image and the included AFLNet source snapshot and adapter patches:

    ./build.sh

Run one isolated, network-disabled campaign with the same cgroup limits used for this delivery. The output path must be empty:

    docker run --rm --network none --cpus=2 --memory=3200m --memory-swap=3200m -v "$PWD/results:/results" scylla-native-fuzz-bench:2026.3.5 bash run.sh /results/scylla-fuzz-30m-YYYYMMDD 30m

AFLNet is run in no-instrumentation, no-forkserver network mode. A small ELF Python command is used only as the placeholder target required by AFLNet; the separately managed ScyllaDB process is the actual TCP service. The adapter parses 9-byte Native Protocol frame headers and feeds response opcode/error state sequences to AFLNet. ScyllaDB itself is not coverage-instrumented, so AFL's bitmap is a helper metric and must not be described as ScyllaDB source coverage.

The campaign keeps one isolated ScyllaDB node alive and drops every non-system keyspace before each testcase. Initial startup clears its data, commitlog, saved-cache, and hints directories. The node uses --smp 1 and --memory 1536M inside a 3,200 MiB container, with 2 CPUs and swap disabled.

## Replay and post-run smoke

Replay all three saved queue representations using a fresh result directory:

    docker run --rm --network none --cpus=2 --memory=3200m --memory-swap=3200m -v "$PWD/results:/results" scylla-native-fuzz-bench:2026.3.5 python3 /opt/benchmark/replay_queue.py /results/scylla-fuzz-30m-YYYYMMDD /results/scylla-fuzz-30m-YYYYMMDD/replay-validation 100

Run the valid-flow smoke after replay:

    docker run --rm --network none --cpus=2 --memory=3200m --memory-swap=3200m -v "$PWD/results:/results" scylla-native-fuzz-bench:2026.3.5 python3 /opt/benchmark/scylla_smoke.py /results/scylla-smoke-post-YYYYMMDD 3

ScyllaDB 2026.3 defaults to tablet-enabled keyspaces. SimpleStrategy is not compatible with tablets, so the smoke CQL explicitly sets tablets = {'enabled': false}. The exact test flows and results are in scylla_smoke.py and protocol-smoke.json.

The central framework experience is maintained only in the framework package's 基准化经验库.md; this standalone ZIP does not duplicate an experience entry.
