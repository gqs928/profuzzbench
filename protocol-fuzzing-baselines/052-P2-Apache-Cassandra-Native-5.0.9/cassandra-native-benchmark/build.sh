#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
docker build --pull --build-arg CASSANDRA_IMAGE="$(sed -n 's/^CASSANDRA_IMAGE=//p' images.env)" \
  --tag cassandra-native-fuzz-bench:5.0.9 .
docker image inspect cassandra-native-fuzz-bench:5.0.9 --format '{{.Id}}' \
  | tee build-logs/image-id.txt
