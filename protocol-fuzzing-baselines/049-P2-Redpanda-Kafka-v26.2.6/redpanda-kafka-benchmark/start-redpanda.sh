#!/usr/bin/env bash
set -euo pipefail

DATA_DIR=${REDPANDA_DATA_DIR:-/var/lib/redpanda/data}
find "${DATA_DIR}" -mindepth 1 -maxdepth 1 -exec rm -rf -- {} +

# rpk replaces itself with the official broker process; AFLNet's -K SIGTERM
# therefore stops the actual broker before the next sample clears its data.
exec /usr/bin/rpk redpanda start \
  --mode dev-container \
  --smp 1 \
  --kafka-addr PLAINTEXT://127.0.0.1:9092 \
  --advertise-kafka-addr PLAINTEXT://127.0.0.1:9092
