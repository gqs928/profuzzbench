# Apache Artemis AMQP 1.0 benchmark

## Target and build

- Target: Apache Artemis 2.57.0, using the official binary distribution. SHA-512 sidecar verification passed; digest: `47d2193b4707bde8c856ee0f7ee623e87722559b8503aaef6ee015496499774a8c9b9492933cc0a52873e95dce73ff825222422996d2a8768a4936b015415e8c`.
- Fuzzer: AFLNet commit `0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732`; archive SHA-256 verification and AMQP parser unit test passed during image build.
- Profile: AMQP 1.0 over loopback TCP/5672, with SASL PLAIN guest/guest in the seed corpus. One broker instance was run with a 1 CPU and 1.2 GiB memory limit; persistence and web console were disabled.
- Version references: [Apache Artemis AMQP documentation](https://artemis.apache.org/components/artemis/documentation/latest/amqp.html), [official Apache Artemis 2.57.0 distribution](https://downloads.apache.org/artemis/artemis/2.57.0/).

## Formal campaign

The AFLNet initial seed dry-run completed before the campaign timer began. The active fuzzing window was 1,802 seconds. `fuzzer_exit_status=0`.

| Metric | Result |
|---|---:|
| Executions | 248 |
| AFLNet queue paths | 7 |
| Newly found paths | 1 |
| Queue cycles completed | 0 |
| Stability | 100.00% |
| AFL bitmap coverage | 0.00% |
| Unique crashes | 0 |
| Unique hangs | 0 |

This is a black-box network campaign. The AFL bitmap value is not Java source coverage; interpret it separately from AFLNet protocol-state paths. The first queue cycle was still in progress at the end of the 30-minute window.

## Post-run validation

- Fresh broker smoke: SASL PLAIN passed and the AMQP 1.0 `connection.open` handshake passed.
- Queue replay: 7/7 files connected and received a response; 5 read-timeout events, 0 resets, and 0 connection errors. Response and timeout counts are non-exclusive because replay continues reading after the first response.
- The formal broker log contains expected rejects/timeouts for malformed or incomplete fuzz inputs; the broker remained available through the campaign. The post-run broker startup log confirms the AMQP acceptor on port 5672.

The fuzzer itself exited successfully after the full window. The outer container wrapper returned status 1 only because its final permission pass attempted to chmod the host-created `broker.log`; this did not affect AFLNet's exit status, saved statistics, or output files. The delivery script excludes that host-created log from the chmod pass.

## Evidence

- Formal results and queue: `amqp-30m/`
- Initial handshake smoke: `protocol-smoke-initial/`
- Post-run handshake, queue replay, and broker log: `protocol-smoke-final/`
- Source/version checks: `../source-lock.json`
