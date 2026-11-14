# RabbitMQ STOMP benchmark

This profile benchmarks RabbitMQ Server 4.4.0 with the bundled `rabbitmq_stomp` plugin through STOMP 1.2 on loopback TCP/61613. It uses the same frame-boundary and response-command adapter contract as the other STOMP profiles, with queue and receipt-driven seeds. This is a black-box state-feedback benchmark, not Erlang source coverage.

Before building the image, run `./prepare-rabbitmq.sh` to verify the official release archive SHA-256 and signature against the bundled RabbitMQ signing key, then extract the distribution. Build AFLNet with `./build-aflnet.sh` and build the pinned Erlang 29.0.6 image with `docker build -t profuzzbench-rabbitmq-stomp:4.4.0 .`. Run a localhost-only mapping and an empty host result directory:

```sh
mkdir -p results
docker run -d --name rabbitmq-stomp-440 -p 127.0.0.1:61613:61613 \
  -v "$PWD/results:/results" profuzzbench-rabbitmq-stomp:4.4.0
python3 protocol_smoke.py
docker exec -d rabbitmq-stomp-440 bash /opt/benchmark/fuzz.sh /results/stomp-30m 1800
```

The smoke check validates STOMP 1.2 negotiation, queue subscription receipt, and message delivery against RabbitMQ's default `/` virtual host. The `host:/` STOMP header must match that vhost; a different host header selects a different RabbitMQ vhost and requires its own user permissions. The formal campaign runs 1,800 seconds after `fuzzer_stats` appears; replay queue samples with `python3 replay_queue.py results/stomp-30m` after it completes. RabbitMQ starts as an unprivileged container user, the generated `admin/admin` user is scoped to the local test node, and Docker publishes only the STOMP port on host loopback.

The generic-unix release is signed by RabbitMQ's release key; its archive, detached signature, and key are included. `source-lock.json` pins the release, Erlang runtime image digest, and AFLNet source commit. After verifying the delivery ZIP and checksum, run `./stop-server-and-remove-image.sh` to remove this profile's exact container and image.
