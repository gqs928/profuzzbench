# OpenSIPS 4.0.3 SIP/UDP fuzz benchmark

This package builds the real OpenSIPS 4.0.3 SIP server with AFLNet edge instrumentation and ASan. The profile is SIP over UDP on loopback port 5060. A small stateless routing script returns a SIP 200 response so valid and malformed requests exercise the real parser and request route. Package memory uses the system allocator; shared memory explicitly selects the compiled `F_PARALLEL_MALLOC` allocator. It does not include TCP/TLS, database-backed registration, or proxy routing.

## Build and smoke test

```sh
./build.sh
```

The validation script checks the server version, sends a SIP OPTIONS request over UDP, and checks the status line and response terminator.

## Run

```sh
docker run --rm --network none --user "$(id -u):$(id -g)" \
  -v "$PWD/results:/work/results" \
  opensips-sip-aflnet:4.0.3 /work/run.sh /work/results/sip-30m 1800
```

The wrapper checks that AFLNet's `last_update - start_time` matches the requested runtime. AFLNet's SIP parser supplies status-code feedback. Queue samples and crash candidates require independent replay before any defect claim.

The formal-run metrics, calibration skips, and independent hang-candidate replay results are documented in `RESULTS.md`. Replay uses a fresh OpenSIPS process for each candidate and follows it with a valid SIP health request.

## Locked inputs

- OpenSIPS tag `4.0.3`, commit `ca1549c1350a455aa73a420fbecaba53d7d451dd`.
- ProFuzzBench AFLNet commit `0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732`.
- Ubuntu 24.04 image digest `sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852`.
- Archive hashes are checked during image construction.
