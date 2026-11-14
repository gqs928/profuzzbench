# Apache Artemis AMQP benchmark

This profile benchmarks Apache Artemis 2.57.0 using the broker's AMQP 1.0 implementation over loopback TCP/5672. The AFLNet adapter segments AMQP version headers and length-prefixed frames, then maps response performative descriptors, including SASL states, to stable protocol-state IDs. The broker process remains alive across testcase connections. This is a black-box state-feedback profile and does not report Java source coverage.

The default formal campaign runs 1,800 seconds after mutation begins. Build with `docker build -t profuzzbench-artemis:2.57.0 .`. The generated broker instance has persistence and web console disabled for this deterministic test profile; run `python3 /opt/benchmark/protocol_smoke.py` inside a started container before running `bash /opt/benchmark/fuzz.sh /results/amqp-30m 1800` against an empty host result directory.

The broker uses the official 2.57.0 binary distribution, verified against Apache's SHA-512 sidecar. The default AMQP 1.0 acceptor is on port 5672, and the `guest` SASL credentials are used by the handshake seeds.
