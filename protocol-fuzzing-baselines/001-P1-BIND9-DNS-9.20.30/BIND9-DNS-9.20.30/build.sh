#!/usr/bin/env bash
set -euo pipefail

package_dir=$(cd "$(dirname "$0")" && pwd)
image=${1:-bind9-dns-aflnet:9.20.30}
log_dir=${2:-"$package_dir/results/build"}
mkdir -p "$log_dir"

(cd "$package_dir" && docker build --progress plain --build-arg MAKE_JOBS=1 -t "$image" .) \
  >"$log_dir/docker-build.log" 2>&1
docker image inspect "$image" --format '{{.Id}}' > "$log_dir/image-id.txt"
docker run --rm --network none --user "$(id -u):$(id -g)" -v "$log_dir:/host-results" \
  --entrypoint /work/validate.sh "$image" /host-results

{
  printf 'base_image=ubuntu:24.04@sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852\n'
  printf 'bind_tag=v9.20.30\n'
  printf 'bind_commit=769c3fb93a0a06b2f1f44b5156c4f7e52f57ef78\n'
  printf 'bind_archive_sha256=83fd27150513e6c7e6154b4867922369e6cd88670225e904f3681fce85fa7782\n'
  printf 'aflnet_commit=0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732\n'
  printf 'aflnet_archive_sha256=251f24bf2dddb8118eab56ef2b90c92b06f67c096c62543659eaaf31a31d955d\n'
  printf 'image_id=%s\n' "$(cat "$log_dir/image-id.txt")"
  printf 'build_time_utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "$log_dir/build-lock.txt"
