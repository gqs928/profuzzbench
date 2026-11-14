# Leafnode 1.12.0 NNTP benchmark

This package benchmarks Leafnode's NNTP service at the latest stable release, 1.12.0. Leafnode is normally launched by inetd with a connected socket on stdin/stdout, so `listener.c` supplies a small TCP/1119 loopback listener and forks one Leafnode protocol session per connection. Each connection begins from a cleared local spool fixture. The harness changes no NNTP parser or command handler logic. It skips Leafnode's one-second post-session PID-reuse delay only in benchmark mode (`LEAFNODE_FAST_EXIT=1`), after the response stream has been flushed.

The container has reference, ASan/AFLNet-instrumented, and gcov builds compiled from the same upstream archive. AFLNet splits NNTP input at CRLF boundaries, maps numeric response codes to states, and recognizes dot-terminated multiline replies. The test profile is anonymous and isolated with Docker `--network none`; it uses no external news server, TLS, fetchnews synchronization, or live article hierarchy. The profile therefore measures the local NNTP service command path and its configured empty spool fixture.

## Build and validate

```sh
chmod +x ./*.sh
./build.sh
./validate.sh profuzzbench/leafnode-nntp:1.12.0 "$PWD/results/validation" 60s
```

The protocol smoke compares response status paths from all three variants for greeting, command, and multiline replies. The fuzzer smoke additionally requires nonzero executions and a nontrivial AFLNet state graph. To replay the resulting queue against the gcov build:

```sh
docker run --rm --network none --user "$(id -u):$(id -g)" \
  -v "$PWD/results:/results" profuzzbench/leafnode-nntp:1.12.0 \
  python3 /opt/benchmark/coverage_replay.py \
    /results/validation/fuzz-smoke/queue /results/validation/coverage-smoke
```

The formal run defaults to 30 minutes:

```sh
docker run --rm --network none --user "$(id -u):$(id -g)" \
  -v "$PWD/results:/results" profuzzbench/leafnode-nntp:1.12.0 \
  bash /opt/benchmark/run.sh /results/nntp-30m 30m
```

Use `results/` for the run's `fuzzer_stats`, IPSM, queue replay, gcov report and checksums. A successful short smoke is not a substitute for the formal run.

The completed formal run is recorded in `results/RESULTS.md`: 1,800 seconds, 2,999 executions, 100 paths, 18.50% stability, no crashes or hangs; gcov replay accepted all 100 queue samples and covered 768/5,982 Leafnode lines. Three malformed samples caused the server to reset the connection while the replay drained the response; these are recorded separately from replay transport errors. Stability was very low and `cycles_done` remained 0, so treat the result as exploratory.

## Pinned sources

- [Leafnode official SourceForge files](https://sourceforge.net/projects/leafnode/files/) — release archive `leafnode-1.12.0.tar.xz`, SHA256 in `source-lock.json`.
- [AFLNet pinned source](https://github.com/aflnet/aflnet/tree/0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732).
- [NNTP, RFC 3977](https://www.rfc-editor.org/rfc/rfc3977).
