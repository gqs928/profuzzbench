# Apache Qpid Broker-J AMQP 1.0 benchmark

## Target and build

- Target: Apache Qpid Broker-J 10.1.1 official binary distribution. SHA-512 verification passed; digest: `4e3cfdb570c9f64d7c5015f491c1183853592447fb81bf0b2a22e28bbdf438280ee77e822ef2e394b90f906115a56cf906c626bbdb785c3d02a55de3b86caaa1`.
- Fuzzer: AFLNet commit `0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732`; archive checksum, build, and AMQP parser unit test passed.
- Profile: AMQP 1.0 over loopback TCP/5672; six binary seeds use SASL PLAIN guest/guest. One broker ran with 1 CPU and 1.2 GiB memory.
- Qpid disables PLAIN on non-TLS ports by default. The test's initial config sets `secureOnlyMechanisms` to `[]`, following the [official Qpid Broker-J 10.1.1 security guide](https://qpid.apache.org/releases/qpid-broker-j-10.1.1/book/Java-Broker-Security.html). This is restricted to a `--network none` container; do not expose this profile on an external network because PLAIN transmits credentials without encryption.
- Release reference: [official Qpid Broker-J 10.1.1 release](https://qpid.apache.org/releases/qpid-broker-j-10.1.1/).

## Formal campaign

The initial seed dry-run completed before the active campaign timer began. The formal window lasted 1,802 seconds; AFLNet exited with status 0.

| Metric | Result |
|---|---:|
| Executions | 396 |
| AFLNet queue paths | 7 |
| Newly found paths | 1 |
| Queue cycles completed | 1 |
| Variable paths | 0 |
| Stability | 100.00% |
| AFL bitmap coverage | 0.00% |
| Unique crashes | 0 |
| Unique hangs | 0 |

This is a black-box network campaign. AFL bitmap coverage is not Java source coverage. One complete queue cycle finished during the 30-minute window.

## Post-run validation

- Fresh broker smoke passed SASL PLAIN and AMQP 1.0 `connection.open`.
- Queue replay: 7/7 files connected and each produced a response; 1 read-timeout event, 0 resets, and 0 connection errors. Response and timeout counts are non-exclusive because the replay continues reading after its first response.
- The saved broker log confirms Broker-J 10.1.1 readiness on TCP 5672.

## Evidence

- Formal results, broker log, and queue: `amqp-30m/`
- Initial and post-run smoke plus queue replay: `protocol-smoke-initial/`, `protocol-smoke-final/`
- Initial config and source/version locks: `../config/qpid-initial-config.json`, `../source-lock.json`
