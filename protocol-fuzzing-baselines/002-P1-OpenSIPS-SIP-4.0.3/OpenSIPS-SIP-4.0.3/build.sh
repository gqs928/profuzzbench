#!/usr/bin/env bash
set -euo pipefail

package_dir=$(cd "$(dirname "$0")" && pwd)
image=${1:-opensips-sip-aflnet:4.0.3}
log_dir=${2:-"$package_dir/results/build"}
mkdir -p "$log_dir"
(cd "$package_dir" && docker build --progress plain --build-arg MAKE_JOBS=1 -t "$image" .) \
  >"$log_dir/docker-build.log" 2>&1
docker image inspect "$image" --format '{{.Id}}' > "$log_dir/image-id.txt"
docker run --rm --network none --user "$(id -u):$(id -g)" -v "$log_dir:/host-results" \
  --entrypoint /work/validate.sh "$image" /host-results
{
  printf 'base_image=ubuntu:24.04@sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852\n'
  printf 'opensips_tag=4.0.3\n'
  printf 'opensips_commit=ca1549c1350a455aa73a420fbecaba53d7d451dd\n'
  printf 'aflnet_commit=0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732\n'
  printf 'image_id=%s\n' "$(cat "$log_dir/image-id.txt")"
  printf 'build_time_utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "$log_dir/build-lock.txt"
