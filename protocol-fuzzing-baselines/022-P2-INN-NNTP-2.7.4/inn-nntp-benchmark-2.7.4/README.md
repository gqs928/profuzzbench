# INN 2.7.4 NNTP protocol baseline

This standalone package benchmarks the reader-facing NNTP service `nnrpd` from official INN 2.7.4. It binds only to loopback TCP/1119 inside a network-isolated container. The setup uses a minimal local active file, read-only anonymous access, and no upstream news feed or TLS.

The package pins the official INN release archive, AFLNet commit, Ubuntu base image digest and package snapshot. The image contains reference, ASan/AFL-instrumented and gcov builds compiled from the same INN archive. The NNTP adapter splits CRLF-delimited client commands, preserves an unterminated final command, maps three-digit reply codes to stable states, and recognizes the dot terminator for multiline server replies.

Build and validate from this directory:

```sh
chmod +x ./*.sh
./build.sh
./validate.sh profuzzbench/inn-nntp:2.7.4 "$PWD/results/validation" 60s
```

The smoke test compares the response-code transcript for CAPABILITIES, MODE READER, DATE, LIST ACTIVE, GROUP, STAT, HELP and QUIT across all three builds. To run the formal baseline:

```sh
mkdir -p results
docker run --rm --network none --user "$(id -u):$(id -g)" --group-add 9 \
  -v "$PWD/results:/results" profuzzbench/inn-nntp:2.7.4 \
  bash /opt/benchmark/run.sh /results/nntp-30m 30m
```

The metric scope is the NNTP reader command path handled by `nnrpd`; this profile does not cover peer-to-peer article feed processing by `innd`, posting/article injection, TLS, or a live Usenet hierarchy. Result claims must be taken from the included `fuzzer_stats`, IPSM, queue replay and smoke evidence. A successful short validation does not replace the 30-minute run.

The completed formal run is recorded in `results/RESULTS.md`: 1,800 seconds, 3,407 executions, 141 paths, 91.25% stability, no crashes or hangs; gcov replay accepted all 141 queue samples and covered 1,002/5,172 `nnrpd` lines. Stability was below 95%, so treat the run as exploratory; `cycles_done` remained 0.

Pinned sources and protocol references:

- [INN 2.7.4 release](https://github.com/InterNetNews/inn/releases/tag/2.7.4)
- [INN official release archive](https://downloads.isc.org/isc/inn/inn-2.7.4.tar.gz)
- [nnrpd manual](https://www.eyrie.org/~eagle/software/inn/docs/nnrpd.html)
- [readers.conf manual](https://www.eyrie.org/~eagle/software/inn/docs/readers.conf.html)
- [NNTP, RFC 3977](https://www.rfc-editor.org/rfc/rfc3977)
- [AFLNet source](https://github.com/aflnet/aflnet/tree/0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732)
