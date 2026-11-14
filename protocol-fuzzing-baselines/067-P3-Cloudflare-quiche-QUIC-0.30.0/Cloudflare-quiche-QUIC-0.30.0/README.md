# Cloudflare quiche 0.30.0 QUIC baseline

This package builds Cloudflare quiche 0.30.0 and its official `quiche-server` example, then runs AFLNet over UDP. The protocol release is pinned to the official `0.30.0` tag (`be47c50`); the source archive SHA-256 is recorded in `source-lock.json`.

The baseline exercises QUIC v1 Initial processing and the server's first Initial/Handshake response. It does not claim a completed TLS handshake or an HTTP/3 request/response: AFLNet sends one client Initial datagram per testcase, the server is reset between testcases, and subsequent handshake packets depend on the server's ephemeral TLS state. The official project itself describes its command-line server as an example application rather than a production server. See the [official quiche README](https://github.com/cloudflare/quiche/blob/0.30.0/README.md).

`cargo-afl` instruments the Rust `quiche` crate and server with LLVM SanitizerCoverage. AFLNet uses a custom QUIC response-state parser and preserves each input as one UDP datagram. The parser reports public QUIC header states only; encrypted transport frames and HTTP/3 semantics are not decoded by the state parser. AFLNet's input cap is set to 65,507 bytes, the maximum IPv4 UDP payload.

The target reports an AFL++ 4.40c forkserver, while AFLNet 2.56b implements the vanilla AFL protocol. The target therefore runs with `AFL_OLD_FORKSERVER=1`, and AFLNet's shared coverage map is expanded to 262,144 bytes for the target's 148,103 instrumented locations. The QUIC response parser includes the required initial state (`0`) before server response states.

## Build and run

```sh
./build.sh
./preflight-benchmark.sh
./run-benchmark.sh /results/quiche-fuzz-30m-YYYYMMDD 30m
```

`build.sh` builds the dedicated image, records the exact image ID and toolchain, generates the host-mounted QUIC Initial seed, and validates its hash and datagram structure. The preflight then checks that the official server returns a QUIC Initial or Handshake packet and runs a 60-second AFLNet trial. The formal run is bounded to 30 minutes. Both runs automatically replay every queue, crash, and hang sample in a fresh server process, verify UDP listener closure, and save the console and JSON evidence. AFLNet can classify a silent UDP response as a hang; replay results distinguish ordinary packet drops from a process crash or a target that remains alive but cannot be stopped.

After the formal run, complete `ACCEPTANCE.md` using the recorded statistics and replay evidence, remove only the dedicated image, then run `python3 package.py`. The package validator refuses to create the ZIP unless all checks pass and the exact image is verified absent.

The Docker image is dedicated to this baseline. After validation and packaging, remove only `cloudflare-quiche-aflnet-bench:0.30.0`; the package records that exact cleanup.
