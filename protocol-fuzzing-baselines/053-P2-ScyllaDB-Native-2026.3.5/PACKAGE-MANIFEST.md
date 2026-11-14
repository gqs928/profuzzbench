# Package contents

- README.md: target scope, build/run instructions, reset behavior, and replay/smoke commands.
- ACCEPTANCE.md: official target identity, formal campaign results, replay classification, post-run smoke, and limitations.
- source-lock.json and images.env: official ScyllaDB manifest digest, AFLNet source commit/checksum, build identity, and resource profile.
- Dockerfile, build.sh, and docker-compose.yml: reproducible, digest-pinned image build and isolated runtime configuration.
- AFLNet source archive, parser adapter, parser tests, patches, dictionary, seeds, and seed manifest: reproducible Native Protocol v4 state-feedback implementation.
- start-scylla.sh, reset-scylla.sh, stop-scylla.sh, run.sh, replay_queue.py, and scylla_smoke.py: lifecycle, formal campaign, replay, and protocol verification.
- build-logs/: final build output, runtime dependency checks, image IDs, and exact cleanup record.
- results/scylla-fuzz-30m-20261111/: complete time-bounded AFLNet result, all queue representations, fuzzer statistics, server log, parameters, and lifecycle evidence.
- results/scylla-fuzz-30m-20261111/replay-validation/: one record and log per replayed sample, replay summary, and target lifecycle logs.
- results/scylla-smoke-post-20261112/: three repetitions of four protocol flows and listener-close verification.

The ZIP does not include a per-protocol experience entry. Shared framework guidance is maintained only in the central framework package's 基准化经验库.md.
