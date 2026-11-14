# RabbitMQ AMQP 1.0 benchmark

## Target and build

- Target: RabbitMQ Server 4.4.0 generic Unix distribution. SHA-256 verification passed (`68c22d5dafa15c0911463aeca73c362d638cd6fb8e407ad39512959c6cc37f0f`) and its detached signature verified with signing key fingerprint `0A9AF2115F4687BD29803A206B73A36E6026DFCA`.
- Runtime: Erlang/OTP 29.0.6, pinned base image `erlang:29.0.6-slim@sha256:04f8492a880e591288974ba5d5572e2a833fa3f9c62deceed207f2336d8d072b`.
- Fuzzer: AFLNet commit `0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732`; archive checksum, build, and AMQP parser unit test passed.
- Profile: AMQP 1.0 over loopback TCP/5672, SASL PLAIN guest/guest; one broker with 1 CPU and 1.2 GiB memory.
- Version references: [RabbitMQ download and release information](https://www.rabbitmq.com/docs/download), [AMQP 1.0 documentation](https://www.rabbitmq.com/docs/amqp).

## Formal campaign

The initial seed dry-run completed before the formal timer began. The campaign ran for 1,801 seconds; AFLNet exited with status 0.

| Metric | Result |
|---|---:|
| Executions | 389 |
| AFLNet queue paths | 7 |
| Newly found paths | 1 |
| Queue cycles completed | 1 |
| Stability | 100.00% |
| AFL bitmap coverage | 0.00% |
| Unique crashes | 0 |
| Unique hangs | 0 |

This is a black-box network campaign. The AFL bitmap value is not Erlang source coverage; read it separately from AFLNet protocol-state paths.

## Post-run validation

- Fresh broker smoke passed SASL PLAIN and AMQP 1.0 `connection.open`.
- Queue replay: 7/7 files connected; 4 received at least one response; 4 read-timeout events, 3 resets, and 0 connection errors. These counters are non-exclusive because replay tracks responses and later read outcomes separately.
- The saved broker log confirms RabbitMQ 4.4.0 startup with the supplied configuration on port 5672.

## Evidence

- Formal results, broker log, and corpus: `amqp-30m/`
- Initial and post-run smoke, queue replay, and broker logs: `protocol-smoke-initial/`, `protocol-smoke-final/`
- Source/version checks and runtime configuration: `../source-lock.json`, `../configs/rabbitmq.conf`
