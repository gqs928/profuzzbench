# BIND 9 DNS/UDP fuzz benchmark

This package builds BIND 9.20.30 and ProFuzzBench AFLNet from checksum-locked source archives. It tests the real `named` DNS/UDP server on loopback port 5353 with AFLNet's DNS response-code state extractor. The source tag, resolved commit, base image digest, archive hashes, image ID, smoke results and fuzzer statistics are retained with the run.

## Build and smoke test

```sh
./build.sh
```

The validation script checks the version banner and sends DNS queries over UDP and TCP to the configured authoritative `example.test` zone. The formal campaign below uses UDP and is run inside a Docker network namespace without publishing the port.

## Run

The default campaign is 30 minutes. Use a shorter duration only for a smoke run.

```sh
docker run --rm --network none --user "$(id -u):$(id -g)" \
  -v "$PWD/results:/work/results" \
  bind9-dns-aflnet:9.20.30 /work/run.sh /work/results/dns-30m 1800
```

A run is complete only when `run.json`, `fuzzer_stats`, the queue and the AFLNet log are present. The wrapper checks that `last_update - start_time` in AFLNet's statistics is within five seconds of the requested duration; an exited container alone does not prove that the campaign ran to time.

## Scope

The target is BIND 9.20.30's authoritative DNS service over UDP. Seeds cover A, AAAA, MX, NS, SOA, TXT, EDNS, recursion desired, unknown record type and malformed DNS headers/names. A smoke test also verifies TCP service availability. The AFLNet run uses its existing DNS adapter, which assigns response states from DNS flag/RCODE fields. TCP stateful request sequences and the DoH/SIG(0) HTTP/2 path are outside this run.

This package reports AFLNet's edge-map feedback, not a separate gcov/LLVM source-line coverage report. It does not cover DoH or DNS/TCP stateful request sequences. Queue samples and crash candidates require separate replay before reporting a defect. `results/` is intentionally kept outside the source lock inputs so another run does not change the locked target.

## Locked inputs

- BIND tag `v9.20.30`, commit `769c3fb93a0a06b2f1f44b5156c4f7e52f57ef78`.
- ProFuzzBench AFLNet commit `0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732`.
- Ubuntu 24.04 image digest `sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852`.
- Source archive hashes are checked before compilation by the Docker build.

BIND 9.20.30 is an ISC extended-support stable release. The upstream 9.20.30 build guide documents the Autotools build system and its required libraries [BIND 9.20.30 build guide](https://bind9.readthedocs.io/en/v9.20.30/chapter10.html). ISC's release page lists the 9.20.30 stable release [ISC BIND](https://www.isc.org/bind/).
