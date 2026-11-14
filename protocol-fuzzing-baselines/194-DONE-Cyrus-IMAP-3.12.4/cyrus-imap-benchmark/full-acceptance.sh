#!/usr/bin/env bash
set -euo pipefail

IMAGE=${1:-cyrus-imap-fuzz}
RESULTS_DIR=${2:-"$(pwd)/results/imap-validation-complete"}
FUZZ_TIME=${3:-60s}
REPEATS=3
PACKAGE_DIR=$(cd "$(dirname "$0")" && pwd)

if [[ -e ${RESULTS_DIR} ]] && [[ -n $(find "${RESULTS_DIR}" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null) ]]; then
  echo "Results directory is nonempty: ${RESULTS_DIR}. Choose a fresh path." >&2
  exit 2
fi
mkdir -p "${RESULTS_DIR}/build-logs" "${RESULTS_DIR}/coverage" "${RESULTS_DIR}/coverage-repeat"
chmod +x "${PACKAGE_DIR}"/*.sh
export BUILD_LOG_DIR="${RESULTS_DIR}/build-logs"

echo "[1/8] Rebuilding the pinned Docker image without layer cache"
printf 'build_command=%s\n' "${PACKAGE_DIR}/build.sh ${IMAGE} --no-cache" > "${RESULTS_DIR}/build-logs/build-mode.txt"
"${PACKAGE_DIR}/build.sh" "${IMAGE}" --no-cache

echo "[2/8] Checking ordinary IMAP behavior against both server builds"
docker run --rm --hostname localhost --network none \
  -v "${PACKAGE_DIR}:/workspace:ro" -v "${RESULTS_DIR}:/results" "${IMAGE}" \
  python3 /workspace/protocol_smoke.py /results/protocol-smoke 10 2>&1 \
  | tee "${RESULTS_DIR}/protocol-smoke.log"

echo "[3/8] Replaying every seed command-by-command for three clean rounds"
python3 "${PACKAGE_DIR}/prepare_seeds.py" "${RESULTS_DIR}/seed-files"
docker run --rm --hostname localhost --network none \
  -v "${PACKAGE_DIR}:/workspace:ro" -v "${RESULTS_DIR}:/results" "${IMAGE}" \
  python3 /workspace/seed_replay.py /results/seed-files /results/seed-replay \
  /home/ubuntu/experiments/cyrus-reference "${REPEATS}" \
  > "${RESULTS_DIR}/seed-replay.log" 2>&1

mkdir -p "${RESULTS_DIR}/fixed-corpus/queue"
index=0
while IFS= read -r seed; do
  printf -v id '%06d' "${index}"
  cp "${seed}" "${RESULTS_DIR}/fixed-corpus/queue/id:${id},orig:$(basename "${seed}")"
  index=$((index + 1))
done < <(find "${RESULTS_DIR}/seed-files" -maxdepth 1 -type f -print | sort)

echo "[4/8] Running three independent AFLNet trials with isolated state"
for run in 1 2 3; do
  printf -v name 'fuzz-run-%02d' "${run}"
  docker run --rm --hostname localhost --network none \
    -v "${PACKAGE_DIR}:/workspace:ro" -v "${RESULTS_DIR}:/results" "${IMAGE}" \
    bash /workspace/run.sh "/results/${name}" "${FUZZ_TIME}" \
    2>&1 | tee "${RESULTS_DIR}/${name}.log"
done

mkdir -p "${RESULTS_DIR}/variable-seeds"
variable_index=0
for run in 1 2 3; do
  printf -v run_name 'fuzz-run-%02d' "${run}"
  variable_dir="${RESULTS_DIR}/${run_name}/queue/.state/variable_behavior"
  if [[ -d ${variable_dir} ]]; then
    while IFS= read -r variable_input; do
      variable_index=$((variable_index + 1))
      printf -v variable_id '%03d' "${variable_index}"
      cp "${variable_input}" "${RESULTS_DIR}/variable-seeds/${run_name}__${variable_id}__$(basename "${variable_input}")"
    done < <(find "${variable_dir}" -maxdepth 1 \( -type f -o -type l \) -name 'id:*' -print | sort)
  fi
done
if [[ ${variable_index} -gt 0 ]]; then
  echo "Replaying ${variable_index} AFLNet variable-behavior testcase(s) three times for diagnosis"
  docker run --rm --hostname localhost --network none \
    -v "${PACKAGE_DIR}:/workspace:ro" -v "${RESULTS_DIR}:/results" "${IMAGE}" \
    python3 /workspace/seed_replay.py /results/variable-seeds /results/variable-replay \
    /home/ubuntu/experiments/cyrus-reference 3 \
    > "${RESULTS_DIR}/variable-replay.log" 2>&1
  variable_id=100000
  while IFS= read -r variable_input; do
    variable_id=$((variable_id + 1))
    printf -v queue_id '%06d' "${variable_id}"
    cp "${variable_input}" "${RESULTS_DIR}/fixed-corpus/queue/id:${queue_id},orig:$(basename "${variable_input}")"
  done < <(find "${RESULTS_DIR}/variable-seeds" -maxdepth 1 -type f -print | sort)
else
  printf 'No variable_behavior testcase was retained by AFLNet.\n' > "${RESULTS_DIR}/variable-replay.log"
fi

echo "[5/8] Replaying each trial queue with the genuinely instrumented gcov build"
for run in 1 2 3; do
  printf -v name 'fuzz-run-%02d' "${run}"
  docker run --rm --hostname localhost --network none \
    -v "${PACKAGE_DIR}:/workspace:ro" -v "${RESULTS_DIR}:/results" "${IMAGE}" \
    bash /workspace/coverage-run.sh "/results/${name}" "/results/coverage/${name}" 0 \
    > "${RESULTS_DIR}/coverage/${name}.log" 2>&1
done

echo "[6/8] Replaying the exact same fixed corpus three times to verify reset stability"
for run in 1 2 3; do
  printf -v name 'run-%02d' "${run}"
  docker run --rm --hostname localhost --network none \
    -v "${PACKAGE_DIR}:/workspace:ro" -v "${RESULTS_DIR}:/results" "${IMAGE}" \
    bash /workspace/coverage-run.sh /results/fixed-corpus "/results/coverage-repeat/${name}" 0 \
    > "${RESULTS_DIR}/coverage-repeat/${name}.log" 2>&1
done

echo "[7/8] Injecting a controlled fault into a separate probe server"
docker run --rm --hostname localhost --network none \
  -v "${PACKAGE_DIR}:/workspace:ro" -v "${RESULTS_DIR}:/results" "${IMAGE}" \
  bash /workspace/fault-probe.sh /results/fault-probe \
  > "${RESULTS_DIR}/fault-probe-driver.log" 2>&1

echo "[8/8] Building acceptance tables and checksums"
set +e
python3 "${PACKAGE_DIR}/acceptance_report.py" "${RESULTS_DIR}"
report_status=$?
set -e
(
  cd "${RESULTS_DIR}"
  find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS
)
if [[ ${report_status} -ne 0 ]]; then
  echo "Evidence collection finished, but one or more acceptance checks remain incomplete. See ${RESULTS_DIR}/acceptance-status.md" >&2
  exit "${report_status}"
fi
echo "PASS: all eight acceptance criteria have auditable evidence in ${RESULTS_DIR}"
