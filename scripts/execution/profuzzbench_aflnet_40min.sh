#!/usr/bin/env bash

# Build the protocol targets and run one 40-minute AFLNet session per target.
# Coverage replay and result archiving are skipped because this is a runtime
# stability check. Final fuzzer_stats and timing are copied to RESULTS_DIR.
# Temporary Dockerfiles enable apt retries for flaky package-mirror connections.

set -euo pipefail

PFBENCH=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
cd "$PFBENCH"

DURATION_SECONDS=${DURATION_SECONDS:-2400}
TEST_TIMEOUT_MS=${TEST_TIMEOUT_MS:-5000}
MAX_PARALLEL=${MAX_PARALLEL:-2}
MAKE_OPT=${MAKE_OPT:--j2}
APT_RETRIES=${APT_RETRIES:-10}
APT_HTTP_PIPELINE_DEPTH=${APT_HTTP_PIPELINE_DEPTH:-0}
APT_MIRROR=${APT_MIRROR:-}
BUILD_RETRIES=${BUILD_RETRIES:-3}
REUSE_BUILT_IMAGES=${REUSE_BUILT_IMAGES:-0}
TARGET_FILTER=${TARGET_FILTER:-}
RUN_ID=${RUN_ID:-$(date -u +%Y%m%dT%H%M%SZ)}
RESULTS_DIR=${RESULTS_DIR:-"/tmp/profuzzbench-aflnet-40min-$RUN_ID"}

TARGETS=(forked-daapd dcmtk dnsmasq tinydtls bftpd lightftp proftpd pure-ftpd live555 kamailio exim openssh openssl)
if [[ -n $TARGET_FILTER ]]; then
  IFS=, read -r -a TARGETS <<< "$TARGET_FILTER"
fi

mkdir -p "$RESULTS_DIR"
SUMMARY="$RESULTS_DIR/summary.csv"
printf 'target,elapsed_seconds,execs_done,paths_total,unique_crashes,unique_hangs,container_exit,passed\n' > "$SUMMARY"
{
  printf 'run_id=%s\n' "$RUN_ID"
  printf 'duration_seconds=%s\n' "$DURATION_SECONDS"
  printf 'max_parallel=%s\n' "$MAX_PARALLEL"
  printf 'make_opt=%s\n' "$MAKE_OPT"
  printf 'apt_retries=%s\n' "$APT_RETRIES"
  printf 'apt_http_pipeline_depth=%s\n' "$APT_HTTP_PIPELINE_DEPTH"
  printf 'apt_mirror=%s\n' "$APT_MIRROR"
  printf 'build_retries=%s\n' "$BUILD_RETRIES"
  printf 'reuse_built_images=%s\n' "$REUSE_BUILT_IMAGES"
  printf 'target_filter=%s\n' "${TARGET_FILTER:-all}"
  printf 'targets=%s\n' "${TARGETS[*]}"
} > "$RESULTS_DIR/manifest.txt"

if ! docker info >/dev/null 2>&1; then
  echo "Cannot access the Docker daemon." >&2
  exit 1
fi

build_target() {
  local target=$1
  local context
  local dockerfile="$RESULTS_DIR/Dockerfile-$target"
  case "$target" in
    forked-daapd) context=subjects/DAAP/forked-daapd ;;
    dcmtk) context=subjects/DICOM/Dcmtk ;;
    dnsmasq) context=subjects/DNS/Dnsmasq ;;
    tinydtls) context=subjects/DTLS/TinyDTLS ;;
    bftpd) context=subjects/FTP/BFTPD ;;
    lightftp) context=subjects/FTP/LightFTP ;;
    proftpd) context=subjects/FTP/ProFTPD ;;
    pure-ftpd) context=subjects/FTP/PureFTPD ;;
    live555) context=subjects/RTSP/Live555 ;;
    kamailio) context=subjects/SIP/Kamailio ;;
    exim) context=subjects/SMTP/Exim ;;
    openssh) context=subjects/SSH/OpenSSH ;;
    openssl) context=subjects/TLS/OpenSSL ;;
    *) echo "Unknown target: $target" >&2; return 2 ;;
  esac

  echo "[$(date -Is)] Building $target from $context"
  if [[ $REUSE_BUILT_IMAGES == 1 ]] && docker image inspect "$target" >/dev/null 2>&1; then
    echo "[$(date -Is)] Reusing existing image $target"
    return 0
  fi
  local -a sed_args=(
    -e "s/apt-get -y update/apt-get -o Acquire::Retries=$APT_RETRIES -o Acquire::ForceIPv4=true -o Acquire::http::Pipeline-Depth=$APT_HTTP_PIPELINE_DEPTH -y update/g"
    -e "s/apt-get -y install/apt-get -o Acquire::Retries=$APT_RETRIES -o Acquire::ForceIPv4=true -o Acquire::http::Pipeline-Depth=$APT_HTTP_PIPELINE_DEPTH -y install/g"
  )
  if [[ -n $APT_MIRROR ]]; then
    if [[ ! $APT_MIRROR =~ ^https?://[A-Za-z0-9.-]+(:[0-9]+)?(/[A-Za-z0-9._/-]+)?$ ]]; then
      echo "APT_MIRROR must be a plain http(s) URL." >&2
      return 2
    fi
  fi
  sed "${sed_args[@]}" "$context/Dockerfile" > "$dockerfile"
  if [[ -n $APT_MIRROR ]]; then
    local mirror_dockerfile="$dockerfile.with-mirror"
    awk -v mirror="${APT_MIRROR%/}" '
      NR == 1 {
        print
        printf "RUN sed -i \"s#http://archive.ubuntu.com/ubuntu#%s#g\" /etc/apt/sources.list\n", mirror
        next
      }
      { print }
    ' "$dockerfile" > "$mirror_dockerfile"
    mv "$mirror_dockerfile" "$dockerfile"
  fi
  local attempt=1
  local attempt_log
  while (( attempt <= BUILD_RETRIES )); do
    attempt_log="$RESULTS_DIR/build-$target-attempt-$attempt.log"
    if docker build --network host --progress=plain --file "$dockerfile" \
      --build-arg "MAKE_OPT=$MAKE_OPT" -t "$target" "$context" \
      >"$attempt_log" 2>&1; then
      cp "$attempt_log" "$RESULTS_DIR/build-$target.log"
      return 0
    fi
    echo "Build attempt $attempt/$BUILD_RETRIES failed for $target; successful Docker layers remain cached." >&2
    attempt=$((attempt + 1))
  done
  cp "$attempt_log" "$RESULTS_DIR/build-$target.log"
  tail -80 "$RESULTS_DIR/build-$target.log" >&2
  return 1
}

run_target() {
  local target=$1
  local image=$target
  local data_dir options container outdir container_exit
  case "$target" in
    forked-daapd)
      data_dir=.
      options="-P HTTP -D 200000 -m none -q 3 -s 3 -E -K -t $TEST_TIMEOUT_MS"
      ;;
    dcmtk)
      data_dir=dcmtk/build/bin
      options="-P DICOM -D 10000 -E -K -m none -t $TEST_TIMEOUT_MS"
      ;;
    dnsmasq)
      data_dir=dnsmasq/src
      options="-P DNS -D 10000 -K -R -q 3 -s 3 -E -m none -t $TEST_TIMEOUT_MS"
      ;;
    tinydtls)
      data_dir=.
      options="-P DTLS12 -D 10000 -q 3 -s 3 -E -K -R -W 30 -m none -t $TEST_TIMEOUT_MS"
      ;;
    bftpd)
      data_dir=bftpd
      options="-m none -P FTP -D 10000 -q 3 -s 3 -E -K -t $TEST_TIMEOUT_MS"
      ;;
    lightftp)
      data_dir=LightFTP/src/Release
      options="-P FTP -D 10000 -q 3 -s 3 -E -K -m none -t $TEST_TIMEOUT_MS"
      ;;
    proftpd)
      data_dir=proftpd
      options="-m none -P FTP -D 10000 -q 3 -s 3 -E -K -t ${TEST_TIMEOUT_MS}+"
      ;;
    pure-ftpd)
      data_dir=pure-ftpd
      options="-m none -P FTP -D 10000 -q 3 -s 3 -E -K -t $TEST_TIMEOUT_MS"
      ;;
    live555)
      data_dir=live555/testProgs
      options="-P RTSP -D 10000 -q 3 -s 3 -E -K -R -m none -t $TEST_TIMEOUT_MS"
      ;;
    kamailio)
      data_dir=kamailio
      options="-m none -P SIP -l 5061 -D 50000 -q 3 -s 3 -E -K -t $TEST_TIMEOUT_MS"
      ;;
    exim)
      data_dir=exim
      options="-P SMTP -D 10000 -q 3 -s 3 -E -K -W 100 -m none -t $TEST_TIMEOUT_MS"
      ;;
    openssh)
      data_dir=openssh
      options="-P SSH -D 10000 -q 3 -s 3 -E -K -W 10 -m none -t $TEST_TIMEOUT_MS"
      ;;
    openssl)
      data_dir=openssl
      options="-P TLS -D 10000 -q 3 -s 3 -E -K -R -W 100 -m none -t $TEST_TIMEOUT_MS"
      ;;
    *) echo "Unknown target: $target" >&2; return 2 ;;
  esac

  outdir="out-aflnet-40min-$target"
  container="pfb-aflnet-40m-${RUN_ID//[^a-zA-Z0-9_.-]/-}-$target"
  local target_dir="$RESULTS_DIR/$target"
  mkdir -p "$target_dir"
  echo "[$(date -Is)] Starting $target for $DURATION_SECONDS seconds (container $container)"

  docker rm -f "$container" >/dev/null 2>&1 || true
  docker run -d -i -t --cpus=1 --name "$container" \
    -e "PFBENCH_OUTDIR=$outdir" \
    -e "PFBENCH_RUN_OPTIONS=$options" \
    -e "PFBENCH_DURATION=$DURATION_SECONDS" \
    -e "PFBENCH_TIMING_FILE=$outdir/run_timing.tsv" \
    --entrypoint /bin/bash "$image" -lc '
      set -e
      helper=/tmp/pfb-aflnet-runtime-check
      mkdir -p "$helper"
      cat >"$helper/timeout" <<"SH"
#!/bin/bash
set +e
start_ns=$(date +%s%N)
/usr/bin/timeout "$@"
status=$?
end_ns=$(date +%s%N)
mkdir -p "$(dirname "$PFBENCH_TIMING_FILE")"
awk -v s="$start_ns" -v e="$end_ns" -v r="$status" "BEGIN { printf \"start_ns\\t%s\\nend_ns\\t%s\\nelapsed_seconds\\t%.3f\\ntimeout_exit\\t%s\\n\", s, e, (e-s)/1000000000, r }" > "$PFBENCH_TIMING_FILE"
exit "$status"
SH
      cat >"$helper/cov_script" <<"SH"
#!/bin/bash
out=${1%/}
printf "Coverage replay was skipped for this AFLNet runtime-stability check.\\n" > "$out/COVERAGE_REPLAY_SKIPPED.txt"
SH
      cat >"$helper/gcovr" <<"SH"
#!/bin/sh
exit 0
SH
      cat >"$helper/tar" <<"SH"
#!/bin/sh
exit 0
SH
      chmod +x "$helper/timeout" "$helper/cov_script" "$helper/gcovr" "$helper/tar"
      export PATH="$helper:$PATH"
      cd /home/ubuntu/experiments
      exec /home/ubuntu/experiments/run aflnet "$PFBENCH_OUTDIR" "$PFBENCH_RUN_OPTIONS" "$PFBENCH_DURATION" 5
    ' >"$target_dir/docker-run-id.txt" || {
      echo "docker run failed for $target" >&2
      return 1
    }

  if ! docker wait "$container" >"$target_dir/container-exit.txt"; then
    echo "docker wait failed for $target" >&2
    docker logs "$container" >"$target_dir/container.log" 2>&1 || true
    docker rm -f "$container" >/dev/null 2>&1 || true
    return 1
  fi
  container_exit=$(cat "$target_dir/container-exit.txt")
  docker logs "$container" >"$target_dir/container.log" 2>&1 || true

  docker cp "$container:/home/ubuntu/experiments/$data_dir/$outdir/fuzzer_stats" \
    "$target_dir/fuzzer_stats" >/dev/null 2>&1 || \
  docker cp "$container:/home/ubuntu/experiments/$data_dir/$outdir/default/fuzzer_stats" \
      "$target_dir/fuzzer_stats" >/dev/null 2>&1 || true
  if [[ ! -s "$target_dir/fuzzer_stats" ]]; then
    local stats_path
    stats_path=$(docker exec "$container" find /home/ubuntu/experiments -type f -name fuzzer_stats -print -quit 2>/dev/null || true)
    if [[ -n $stats_path ]]; then
      docker cp "$container:$stats_path" "$target_dir/fuzzer_stats" >/dev/null 2>&1 || true
    fi
  fi
  docker cp "$container:/home/ubuntu/experiments/$data_dir/$outdir/run_timing.tsv" \
      "$target_dir/run_timing.tsv" >/dev/null 2>&1 || true
  docker cp "$container:/home/ubuntu/experiments/$data_dir/$outdir/COVERAGE_REPLAY_SKIPPED.txt" \
    "$target_dir/COVERAGE_REPLAY_SKIPPED.txt" >/dev/null 2>&1 || true
  docker rm "$container" >/dev/null

  local elapsed execs paths crashes hangs passed
  elapsed=$(awk -F '\t' '$1=="elapsed_seconds" {print $2}' "$target_dir/run_timing.tsv" 2>/dev/null || true)
  execs=$(awk -F: '$1 ~ /^[[:space:]]*execs_done[[:space:]]*$/ {gsub(/[[:space:]]/, "", $2); print $2}' "$target_dir/fuzzer_stats" 2>/dev/null || true)
  paths=$(awk -F: '$1 ~ /^[[:space:]]*paths_total[[:space:]]*$/ {gsub(/[[:space:]]/, "", $2); print $2}' "$target_dir/fuzzer_stats" 2>/dev/null || true)
  crashes=$(awk -F: '$1 ~ /^[[:space:]]*unique_crashes[[:space:]]*$/ {gsub(/[[:space:]]/, "", $2); print $2}' "$target_dir/fuzzer_stats" 2>/dev/null || true)
  hangs=$(awk -F: '$1 ~ /^[[:space:]]*unique_hangs[[:space:]]*$/ {gsub(/[[:space:]]/, "", $2); print $2}' "$target_dir/fuzzer_stats" 2>/dev/null || true)
  if [[ -z $execs || -z $crashes || -z $hangs ]]; then
    local plain_log execs_display
    plain_log=$(mktemp "$target_dir/container-plain.XXXXXX")
    sed -E 's/\x1B\[[0-9;?]*[[:alpha:]]//g' "$target_dir/container.log" | tr '\r' '\n' > "$plain_log"
    if [[ -z $execs ]]; then
      execs_display=$(grep -oE 'total execs[[:space:]]*:[[:space:]]*[0-9]+([.][0-9]+)?[kKmM]?' "$plain_log" | tail -1 | sed -E 's/.*:[[:space:]]*//' || true)
      if [[ $execs_display =~ ^([0-9]+([.][0-9]+)?)([kKmM])?$ ]]; then
        execs=$(awk -v n="${BASH_REMATCH[1]}" -v suffix="${BASH_REMATCH[3]}" 'BEGIN { m=1; if (suffix=="k" || suffix=="K") m=1000; else if (suffix=="m" || suffix=="M") m=1000000; printf "%.0f", n*m }')
      fi
    fi
    if [[ -z $crashes ]]; then
      crashes=$(grep -oE 'uniq crashes[[:space:]]*:[[:space:]]*[0-9]+' "$plain_log" | tail -1 | grep -oE '[0-9]+$' || true)
    fi
    if [[ -z $hangs ]]; then
      hangs=$(grep -oE 'uniq hangs[[:space:]]*:[[:space:]]*[0-9]+' "$plain_log" | tail -1 | grep -oE '[0-9]+$' || true)
    fi
    rm -f "$plain_log"
  fi
  if [[ -z $paths ]]; then
    paths=$(grep -c 'replayable-queue/id:' "$target_dir/container.log" 2>/dev/null || true)
  fi
  elapsed=${elapsed:-0}; execs=${execs:-0}; paths=${paths:-0}; crashes=${crashes:-0}; hangs=${hangs:-0}
  passed=no
  if (( container_exit == 0 )) && \
    awk -v e="$elapsed" -v min="$DURATION_SECONDS" 'BEGIN {exit !(e >= min-5)}' && \
    (( execs > 0 )); then
    passed=yes
  fi
  printf '%s,%s,%s,%s,%s,%s,%s,%s\n' "$target" "$elapsed" "$execs" "$paths" "$crashes" "$hangs" "$container_exit" "$passed" >> "$SUMMARY"
  printf '%s: elapsed=%ss execs=%s paths=%s crashes=%s hangs=%s container_exit=%s PASS=%s\n' \
    "$target" "$elapsed" "$execs" "$paths" "$crashes" "$hangs" "$container_exit" "$passed"
  [[ $passed == yes ]]
}

echo "Results: $RESULTS_DIR"
echo "Building ${#TARGETS[@]} AFLNet target images sequentially (MAKE_OPT=$MAKE_OPT)."
for target in "${TARGETS[@]}"; do
  build_target "$target" || exit 1
done

echo "Starting ${#TARGETS[@]} AFLNet runs with concurrency capped at $MAX_PARALLEL."
active=0
failures=0
for target in "${TARGETS[@]}"; do
  run_target "$target" >"$RESULTS_DIR/run-$target.log" 2>&1 &
  active=$((active + 1))
  if (( active >= MAX_PARALLEL )); then
    if ! wait -n; then failures=1; fi
    active=$((active - 1))
  fi
done
while (( active > 0 )); do
  if ! wait -n; then failures=1; fi
  active=$((active - 1))
done

echo "Run summary: $SUMMARY"
cat "$SUMMARY"
if (( failures != 0 )) || [[ $(wc -l < "$SUMMARY") -ne $((${#TARGETS[@]} + 1)) ]] || grep -q ',no$' "$SUMMARY"; then
  echo "One or more targets failed the 40-minute AFLNet check." >&2
  exit 1
fi

echo "All ${#TARGETS[@]} targets completed the requested AFLNet runtime check."
