# open62541 1.5.10 OPC UA/TCP fuzz baseline

This package builds the upstream OSS-Fuzz `fuzz_tcp_message` target from open62541 1.5.10 and runs it with libFuzzer. The profile covers one arbitrary byte stream sent to a fresh, in-process open62541 server over loopback TCP port 4840 per fuzz iteration. It does not establish an OPC UA session or replay a multi-message client conversation, and it does not cover UDP discovery, mDNS, or other open62541 fuzz targets.

## Build and smoke test

```sh
./build.sh
./run.sh smoke
```

The local patch makes the upstream harness reusable across libFuzzer iterations by using an atomic server-loop flag and resetting it for every input, disables mDNS for this isolated TCP profile, and suppresses only UBSan's function-pointer type check on callback tables that Clang reports as mismatched. AddressSanitizer and the remaining undefined-behavior checks stay enabled. The source archive, patch and container build log are checksum-locked.

## Formal run

```sh
./run.sh formal
```

The script runs libFuzzer for 1,800 seconds with one fork-mode worker, a 5-second per-input timeout, a 2 GiB libFuzzer RSS limit, a 3 GiB container memory limit and one CPU. Fork mode isolates slow or timed-out inputs so one candidate does not end the whole campaign; every timeout artifact is retained for separate replay. The container has no network access; the target binds only to its own loopback. All 1,324 upstream generated corpus files are preserved in `seeds/upstream-corpus/`; because this target starts a new server and sends one standalone TCP message per input, `seeds/formal-corpus/` uses a deterministic representative for each of the 35 message/service-request categories plus a valid HEL seed. The selection map records the source file and hash for every representative. The upstream binary-message dictionary is also used. Raw libFuzzer output, final corpus, artifacts, run metadata and image identity are retained under `results/`.

## Locked inputs

- Upstream release: open62541 `v1.5.10`, commit `93c3bdfc9ea4718b503c6cbf57876237addd0f2c`.
- Upstream OSS-Fuzz target: `tests/fuzz/fuzz_tcp_message.cc`.
- Source tarball SHA-256: `4dbfa3e856dc60726ce92f25d51e5858faeb7625b3b8c2dd13f433a6df1d1771` (includes the exact release submodules).
- Base image: Ubuntu 24.04 at digest `sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852`; the resolved local image ID, container image digest and package versions are recorded in `results/build/`.
- Patch hash is recorded in `patch-checksums.sha256`; source archive hash is recorded in `source-checksums.sha256`.

The shared framework experience library is maintained separately and is intentionally not included in this protocol package.
