# MongoDB Server 9.0.8 — MongoDB Wire Protocol benchmark

This profile targets the official MongoDB Server `9.0.8` linux/amd64 image, pinned by manifest digest. The release notes identify 9.0.8 as the November 10, 2026 patch release. The lock file records the image digest and the server build's Git version.

The benchmark covers unauthenticated standalone TCP exchanges using OP_MSG. It does not cover TLS, authentication, compressed messages, legacy wire opcodes, replica sets, sharding, or the full MongoDB command surface. The seeds exercise `hello`, `ping`, `buildInfo`, `listDatabases`, and a small create/insert/find/delete flow.

The official release binary is not AFL-instrumented. AFLNet therefore runs in `-n` mode with a MongoDB wire-frame parser and response-state feedback. `bitmap_cvg` describes the fuzzer helper only; it is not MongoDB Server source coverage. AFLNet requires its supervised target process to exit after each input, while `mongod` is a persistent server. The profile therefore uses a small compiled helper as AFLNet's per-input target and the AFLNet cleanup hook to restart `mongod` with an empty WiredTiger dbPath on tmpfs before every testcase. The helper is terminated after the exchange, and MongoDB cold-start time is included in each execution.

## Build and verify

```bash
./build.sh
docker compose --env-file images.env run --rm fuzz \
  python3 /opt/benchmark/mongodb_smoke.py /results/smoke-pre 3
docker compose --env-file images.env run --rm fuzz \
  /opt/benchmark/run.sh /results/smoke-fuzz-60s 60s
```

After the parser tests and short fuzz smoke pass, run the 30-minute campaign:

```bash
docker compose --env-file images.env run --rm fuzz \
  /opt/benchmark/run.sh /results/fuzz-30m 30m
```

Replay the completed queue against a fresh MongoDB process per sample, then repeat the valid protocol smoke:

```bash
docker compose --env-file images.env run --rm fuzz \
  python3 /opt/benchmark/replay_queue.py \
  /results/fuzz-30m /results/fuzz-30m/replay-validation
docker compose --env-file images.env run --rm fuzz \
  python3 /opt/benchmark/mongodb_smoke.py /results/smoke-post-fuzz 3
```

The formal report must retain raw AFLNet statistics, queue replay outcomes, process/listener cleanup checks, image identity, seed checksums, and package checksums. Do not report helper bitmap as server coverage. The aggregated automation-framework lessons belong in the central `基准化经验库.md`, not in this protocol package.

The completed campaign, replay, and post-fuzz smoke evidence is summarized in [ACCEPTANCE.md](ACCEPTANCE.md) and retained under `results/`.
