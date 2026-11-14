# Apache ActiveMQ Artemis STOMP benchmark

This profile benchmarks the Apache ActiveMQ Artemis 2.57.0 binary release through its STOMP 1.2 acceptor on loopback TCP/61613. The harness uses STOMP NUL frame boundaries, stable response-command state IDs, queue send/subscribe seeds, and the official Apache SHA-512-verified distribution. It is a black-box state-feedback benchmark and does not claim Java source coverage.

The image bundles the official Eclipse Temurin JRE 21.0.13+9 archive, checked against its SHA-256, and AFLNet at the commit recorded in `source-lock.json`. Build the host adapter with `./build-aflnet.sh`, then build the target image with `docker build -t profuzzbench-artemis-stomp:2.57.0 .`. Run it with a localhost-only port mapping and an empty host result directory:

```sh
mkdir -p results
docker run -d --name artemis-stomp-2570 -p 127.0.0.1:61613:61613 \
  -v "$PWD/results:/results" profuzzbench-artemis-stomp:2.57.0
python3 protocol_smoke.py
docker exec -d artemis-stomp-2570 bash /opt/benchmark/fuzz.sh /results/stomp-30m 1800
```

The corpus omits an un-terminated final frame because a conforming broker waits for the NUL terminator during seed calibration; that parser boundary remains covered by `parser-test.c` and `fixtures/truncated-frame.stomp`. The smoke check verifies STOMP 1.2 negotiation, queue subscription receipt, and message delivery. The formal campaign counts 1,800 seconds from the first `fuzzer_stats` file and stores the unmodified AFLNet outputs under `results/stomp-30m/`. Replay queue samples with `python3 replay_queue.py results/stomp-30m` after the campaign. Verify the delivery ZIP and checksum, then run `./stop-server-and-remove-image.sh` to remove this profile's exact container and image.

The broker instance is created at image build time with persistence and the web console disabled. Artemis retains its default multi-protocol acceptor on 61616, but this profile does not publish that port; the dedicated STOMP acceptor listens on 61613 inside the container and Docker publishes it only on host loopback. The creation flags disable the separate AMQP, MQTT, and HornetQ acceptors.
