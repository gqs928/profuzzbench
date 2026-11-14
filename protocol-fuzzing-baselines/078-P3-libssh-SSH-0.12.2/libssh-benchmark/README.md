# libssh 0.12.2 SSH server fuzz benchmark

This package benchmarks the latest stable libssh release using the upstream
`ssh_server_fuzzer` target for a single 30-minute libFuzzer campaign. The
upstream harness sends mutated SSH peer input through the libssh server state
machine over a local `socketpair`; it does not expose a TCP listener. The
upstream fuzzing mode enables the `none` cipher/MAC so runs can progress past
SSH key exchange reproducibly, and disables `exec()` support to keep fuzzed
configuration and channel behavior from invoking external commands.

The source archive is pinned by SHA-256 and its detached release signature is
verified against the bundled signing key and the primary fingerprint
`88A228D89B07C2C77D0C780903D5DF8CFDD3E8E7`. The container build instruments
the libssh library and harness with LLVM libFuzzer coverage, AddressSanitizer,
and UndefinedBehaviorSanitizer. The shipped upstream SSH server corpus is the
initial corpus; mutations and any sanitizer artifacts are captured in each
run directory.

## Build and run

From this directory:

```sh
docker build --pull=false -t libssh-server-bench:0.12.2 .
mkdir -p results/libssh-server-preflight-60s
docker run --rm -v "$PWD/results:/work/results" libssh-server-bench:0.12.2 \
  /work/results/libssh-server-preflight-60s 60
mkdir -p results/libssh-server-30m
docker run --rm -v "$PWD/results:/work/results" libssh-server-bench:0.12.2 \
  /work/results/libssh-server-30m 1800
```

For this delivery, the 60-second preflight and the formal 1,800-second result
are in `results/`. The formal run completed in 1,801 seconds with 1,242,579
executions, 3,278 coverage counters, 10,056 features, 689 executions/second,
and 526 MB peak RSS; the process exited 0 with no ASan/UBSan errors or artifact
files. The preflight completed in 62 seconds with 50,606 executions and no
sanitizer errors. The source verification, final build lock, and exact image
metadata are recorded in `build-evidence/`. These metrics describe the
in-process SSH server parser target and are not TCP throughput or network-daemon
coverage. `ACCEPTANCE.md` records the full run criteria and results.
