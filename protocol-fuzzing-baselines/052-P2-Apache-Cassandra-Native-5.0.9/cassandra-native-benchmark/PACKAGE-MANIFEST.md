# Package contents

- `ACCEPTANCE.md`: version lock, formal campaign metrics, reproducible decoder-exception finding, replay and smoke outcomes, and limitations.
- `source-lock.json`, `images.env`: release, image digest, fuzzer source, build image ID, and run profile.
- `Dockerfile`, `build.sh`, `docker-compose.yml`: reproducible benchmark image and isolated runtime configuration.
- `cassandra_aflnet.inc`, parser fixture/test, AFLNet patches, seeds, dictionary, and helper scripts: Cassandra framing, response-state extraction, reset, replay, and smoke implementation.
- `results/cassandra-fuzz-30m-20261111/`: the complete 30-minute AFLNet output, including all three queue representations, fuzzer statistics, target logs, and lifecycle log.
- `results/cassandra-replay-full-20261111-v2/`: per-sample records and logs for all 81 raw/KL/IPSM queue entries.
- `results/cassandra-replay-suspects-v2/` and `results/cassandra-suspect-candidates/`: isolated 3/3 reproduction of the decoder exception and the exact raw/KL inputs.
- `results/cassandra-smoke-post-30m/`: post-replay valid-protocol smoke evidence.
- `results/cassandra-preflight-10s-noforkfix/`: successful short regression preflight for the AFLNet no-forkserver cleanup fix; it is not part of formal campaign metrics.
- `build-logs/`: image identity and cleanup records, plus the initial cached build log.

The shared benchmark experience is maintained only in the central `基准化经验库.md`, not duplicated in this protocol package.
