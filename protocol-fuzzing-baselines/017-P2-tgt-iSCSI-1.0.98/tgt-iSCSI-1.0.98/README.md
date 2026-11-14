# tgt iSCSI stateful-fuzz baseline

This package benchmarks the iSCSI target path in **tgt 1.0.98** with AFLNet. It builds reference, AFL-instrumented, and gcov-instrumented variants from the same upstream release archive. Source archives are pinned by SHA-256, and the iSCSI adapter parses the binary Basic Header Segment, Additional Header Segment length, 24-bit data-segment length, and four-byte padding.

The target wrapper creates an isolated local target and a small temporary backing store for each AFLNet testcase. A deterministic initiator performs Security and Operational Login negotiation and a SCSI INQUIRY. Seed capture is based on that successful exchange; malformed-length inputs are included as separate fuzz seeds. Response states encode opcode, SCSI status, and Login Response status class/detail.

## Build and validate

From this directory, build the pinned image and run an isolated protocol smoke test plus a short AFLNet run:

```sh
docker build -t profuzzbench/tgt-aflnet:1.0.98 .
./validate.sh profuzzbench/tgt-aflnet:1.0.98 "$PWD/results/iscsi-validation" 60s
```

The container uses `--network none`; the service binds only inside its private container network namespace. No host port is published. The acceptance script checks the parser unit test at image build, a valid Login and INQUIRY exchange, seed generation, AFLNet executions, and a nonempty response-state graph.

## Thirty-minute run

After validation, generate a fresh seed set and run the full baseline:

```sh
mkdir -p results/iscsi-30m/seeds
docker run --rm --network none --user "$(id -u):$(id -g)" \
  -v "$PWD:/workspace:ro" \
  -v "$PWD/results/iscsi-30m:/results" profuzzbench/tgt-aflnet:1.0.98 \
  bash /opt/benchmark/smoke.sh /results/protocol-smoke
find results/iscsi-30m/protocol-smoke/seeds -maxdepth 1 -type f -name '*.bin' -exec cp {} results/iscsi-30m/seeds/ \;
docker run --rm --network none --user "$(id -u):$(id -g)" \
  -v "$PWD:/workspace:ro" \
  -v "$PWD/results/iscsi-30m:/results" -e SEEDS=/results/seeds \
  profuzzbench/tgt-aflnet:1.0.98 \
  bash /opt/benchmark/run.sh /results/fuzz-30m 30m
```

The result includes `fuzzer_stats`, queue/crash artifacts, the IPSM graph, and a SHA-256 manifest. For each completed baseline, remove its image after copying and verifying all evidence.

## Scope and limitations

- iSCSI over plaintext TCP/3260, one local target and one file-backed LUN.
- Covers Login negotiation and a SCSI INQUIRY seed path; it does not benchmark CHAP, TLS, RDMA/iSER, multipath, or sustained block I/O throughput.
- A short acceptance run verifies setup, protocol handling, instrumentation, and state feedback. It is not a security audit and does not establish the absence or presence of vulnerabilities.

## Pinned sources

- tgt 1.0.98: official [upstream repository](https://github.com/fujita/tgt), tag `v1.0.98`.
- AFLNet: ProFuzzBench AFLNet commit `0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732`.
- iSCSI: [RFC 7143](https://www.rfc-editor.org/rfc/rfc7143).
- Archive checksums: `source-checksums.sha256`; the image build checks both source archives before compiling.
