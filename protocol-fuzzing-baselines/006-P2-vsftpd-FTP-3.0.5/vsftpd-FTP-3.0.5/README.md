# vsftpd 3.0.5 FTP/TCP fuzz baseline

This package builds the upstream vsftpd 3.0.5 server and AFLNet from checksum-locked archives. It exercises the actual FTP control service on loopback port 2121 with AFLNet's FTP state extractor. The source signature, source hashes, base-image digest, build identity, real-service transcript checks, fuzzer statistics, queue, and source-coverage replay are retained under `results/`.

## Build and validate

```sh
./build.sh
```

The build compiles reference, AFL/ASan, and gcov variants. Validation compares three independent FTP control transcripts from the reference and instrumented variants and runs a short AFLNet preflight.

## Run the 30-minute campaign

```sh
docker run --rm --network none \
  -v "$PWD/results:/work/results" \
  vsftpd-ftp-aflnet:3.0.5 /work/run.sh ftp-30m 1800
```

`run.sh` checks both the external elapsed time and AFLNet's `fuzzer_stats`, then replays the queue on fresh gcov-instrumented server processes and writes line, branch, and function coverage. A run counts as complete only when the requested duration and AFLNet statistics agree.

## Scope

The benchmark covers FTP control commands over TCP/IPv4 loopback. It uses anonymous login and a read-only server configuration; active/passive data channels, file transfer, TLS, and external network access are disabled. Ten deterministic seed sessions cover login, capability and status commands, path navigation, option changes, invalid users and commands, and session reset. The formal target uses one client session per monitored process so AFLNet observes the process serving the fuzzed session.

## Locked inputs

- vsftpd release: `3.0.5`, official source signature checked with the retained release keyring; signer fingerprint `67A2AB4F41F9972C21F6BF667B89011BCAE1CFEA`.
- AFLNet: commit `0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732`.
- Ubuntu 24.04 base image: `sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852`.
- `source-checksums.sha256` locks both source archives before compilation.

The test configuration intentionally disables seccomp and data channels for the isolated local harness; it must not be used as a production FTP configuration. The shared framework experience library is maintained separately and is not copied into this protocol ZIP.

Create the deterministic delivery archive with `./package.py /path/to/vsftpd-FTP-3.0.5.zip`; the command writes a matching `.sha256` file.
