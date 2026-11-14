#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
CONTAINER=nginx-rtmp-30m
IMAGE=nginx-rtmp-aflnet:1.30.6-module-1.2.2
mkdir -p "$ROOT/results"
{
  printf 'container=%s\n' "$CONTAINER"
  if docker container inspect "$CONTAINER" >/dev/null 2>&1; then
    state="$(docker inspect --format '{{.State.Status}}' "$CONTAINER")"
    if [[ "$state" == running ]]; then docker stop -t 30 "$CONTAINER" >/dev/null; fi
    docker rm "$CONTAINER" >/dev/null
    printf 'container_removed=yes\n'
  else
    printf 'container_removed=already-absent\n'
  fi
  printf 'image=%s\n' "$IMAGE"
  if docker image inspect "$IMAGE" >/dev/null 2>&1; then
    docker image rm "$IMAGE" >/dev/null
    printf 'image_removed=yes\n'
  else
    printf 'image_removed=already-absent\n'
  fi
} > "$ROOT/results/cleanup.txt"
