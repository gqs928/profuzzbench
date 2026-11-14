# Memcached ASCII/TCP protocol benchmark

This directory adapts Memcached's ASCII protocol over TCP for repeatable, state-aware AFLNet testing. The target's normal protocol code is not patched. The AFLNet parser patch is a separate benchmark adapter; a reference binary is built from the same pinned Memcached commit for behavior comparison.

## Scope and state model

- Target: Memcached ASCII protocol, TCP/11211; UDP and the binary protocol are out of scope.
- AFLNet understands CRLF command boundaries and the byte-counted bodies of `set`, `add`, `replace`, `append`, `prepend`, and `cas` requests. An incomplete/malformed storage frame is kept as one tail region rather than splitting value bytes into fake commands.
- Response state IDs: `0` initial; `1 VERSION`; `2 STAT`; `3 VALUE`; `4 END`; `5 STORED`; `6 NOT_STORED`; `7 EXISTS`; `8 NOT_FOUND`; `9 DELETED`; `10 TOUCHED`; `11 OK`; `12 ERROR`; `13 CLIENT_ERROR`; `14 SERVER_ERROR`; `99` unknown/future response.
- `run.sh` runs AFLNet with `-P MEMCACHED -E -K -R`, so the request parser and response-state feedback are active, the server process is reset between test cases, and replayable message sequences are retained.

## Build in Kali

The base image is digest-pinned. Ubuntu packages come from the dated [Ubuntu Snapshot Service](https://snapshot.ubuntu.com/), and AFLNet and Memcached are fetched at fixed commits. The image writes those identities and installed toolchain versions to `build-versions.txt`.

```bash
chmod +x ./*.sh
./build.sh memcached-fuzz --network=host --build-arg MAKE_OPT=-j1
```

If Docker's build network still cannot resolve hosts, get a current IP for the snapshot service from Kali and pass it as a host mapping (the address can change):

```bash
SNAPSHOT_IP=$(getent ahostsv4 snapshot.ubuntu.com | awk 'NR==1 {print $1}')
GITHUB_IP=$(getent ahostsv4 github.com | awk 'NR==1 {print $1}')
./build.sh memcached-fuzz --network=host \
  --add-host="snapshot.ubuntu.com:${SNAPSHOT_IP}" \
  --add-host="github.com:${GITHUB_IP}" \
  --build-arg MAKE_OPT=-j1
```

Host mappings are only a workaround for Docker DNS failure; their addresses can change. `build.sh` saves `build-logs/docker-build.log`, the resolved commit/package manifest, image ID, and hashes of the build inputs.

## Quick preflight

```bash
./validate.sh memcached-fuzz "$PWD/memcached-validation" 60s
```

It compares normal responses from the unmodified and instrumented binaries, performs an AFLNet state-aware smoke run, and verifies that a valid IPSM graph with at least two states and one edge was produced.

## Full eight-item acceptance run

```bash
./acceptance.sh memcached-fuzz "$PWD/results/memcached-acceptance" 30m
```

The default 30-minute run creates a reviewable archive next to the result directory. It includes:

- exact protocol request/response transcripts for reference and instrumented builds;
- ten fresh-server replays of `seed-business`, response-state traces, and per-run gcov counter signatures;
- AFLNet `fuzzer_stats`, queue, crash/hang folders, `ipsm.dot`, and a Graphviz-rendered plain graph;
- coverage-over-time CSV and detailed gcovr HTML, with an explicit positive-coverage check for `memcached.c`, `proto_text.c`, `proto_parser.c`, and `items.c`;
- a controlled, test-only crash injection: AFLNet must record the abort and the sample must abort again when replayed. The hook and seed are created under `/tmp` inside the disposable container and never alter the production source/image;
- build identity, input source snapshot, and SHA-256 checksums.

The single-seed repeatability check requires ten independent runs to produce the same response-state sequence and exact response hash. Aggregate line/branch coverage may vary by at most 0.5 percentage points across runs; raw `.gcda` hashes are recorded for diagnosis because byte-level counter files can differ while the protocol response and aggregate coverage remain stable. A protocol mismatch or coverage spread above the limit fails acceptance and leaves each run's logs for diagnosis. Fuzzer-generated `variable_paths` are also saved in `variable-paths.txt` and reported in the summary for review.

## Manual commands

Run AFLNet for 30 minutes:

```bash
mkdir -p "$PWD/results"
docker run --rm \
  -v "$PWD:/workspace:ro" \
  -v "$PWD/results:/results" \
  memcached-fuzz bash /workspace/run.sh aflnet /results/memcached-30m '' 30m 5
```

Generate coverage after the run:

```bash
docker run --rm \
  -v "$PWD:/workspace:ro" \
  -v "$PWD/results:/results" \
  memcached-fuzz bash /workspace/cov_script.sh /results/memcached-30m 5
```

Reports are in `results/memcached-30m/cov_over_time.csv` and `results/memcached-30m/cov_html/index.html`. `clean.sh` deliberately does not kill system-wide Memcached processes; AFLNet's `-K` terminates its own per-test server child so volatile cache state is discarded safely.

## Evidence status

The previous AFLNwe experiment and its gcovr report are useful preliminary results, but they do not prove AFLNet state feedback, the IPSM, ten stable replays, or crash recording. Do not label all eight items passed until the new `acceptance.sh` run completes successfully in Kali. See `ACCEPTANCE.md` for the item-by-item evidence mapping.
