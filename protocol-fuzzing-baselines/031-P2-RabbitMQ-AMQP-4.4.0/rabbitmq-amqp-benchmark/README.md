# RabbitMQ AMQP benchmark

This profile benchmarks RabbitMQ Server 4.4.0 over AMQP 1.0/TCP on loopback port 5672. RabbitMQ 4.4 supports AMQP 1.0 natively; the profile uses the broker's native SASL PLAIN path with the loopback-only `guest` account. The custom AFLNet adapter segments the AMQP protocol header and length-prefixed frames and maps SASL/AMQP performative descriptors to stable response states. This is a black-box state-feedback profile, not Erlang source coverage.

The default formal campaign runs 1,800 seconds after mutation begins. Build with `docker build -t profuzzbench-rabbitmq:4.4.0 .`; run `python3 /opt/benchmark/protocol_smoke.py` in a started container to verify SASL and connection-open, then run `bash /opt/benchmark/fuzz.sh /results/amqp-30m 1800` with an empty results directory mounted at `/results`.
