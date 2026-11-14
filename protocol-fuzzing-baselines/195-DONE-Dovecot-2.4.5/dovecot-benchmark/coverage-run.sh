#!/usr/bin/env bash
set -euo pipefail

QUEUE_ROOT=${1:?用法：coverage-run.sh AFLNet结果目录 输出目录 [最多回放数]}
OUTDIR=${2:?缺少输出目录}
MAX_INPUTS=${3:-0}
WORKDIR=/home/ubuntu/experiments
SOURCE_DIR=${WORKDIR}/src-gcov
PREFIX=${DOVECOT_GCOV_PREFIX:-${WORKDIR}/dovecot-gcov}
QUEUE_DIR=${QUEUE_ROOT}/queue
[[ -d ${QUEUE_DIR} ]] || QUEUE_DIR=${QUEUE_ROOT}
[[ -d ${QUEUE_DIR} ]] || { echo "语料目录不存在：${QUEUE_ROOT}" >&2; exit 2; }
[[ -d ${SOURCE_DIR} ]] || { echo "缺少独立 gcov 源码构建：${SOURCE_DIR}" >&2; exit 2; }
if [[ -e ${OUTDIR} ]] && [[ -n $(find "${OUTDIR}" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null) ]]; then
  echo "覆盖率结果目录非空，请选择新目录：${OUTDIR}" >&2
  exit 2
fi
mkdir -p "${OUTDIR}/replay-log"
export DOVECOT_GCOV_PREFIX=${PREFIX}
export DOVECOT_CONFIG=/workspace/dovecot.conf
export PATH="${PREFIX}/bin:${PREFIX}/sbin:${PREFIX}/libexec:${PATH}"
export LD_LIBRARY_PATH="${PREFIX}/lib${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"

mapfile -d '' INPUTS < <(find "${QUEUE_DIR}" -maxdepth 1 -type f -name 'id:*' -print0 | sort -z)
if ((${#INPUTS[@]} == 0)); then
  mapfile -d '' INPUTS < <(find "${QUEUE_DIR}" -maxdepth 1 -type f -print0 | sort -z)
fi
if [[ ${MAX_INPUTS} -gt 0 ]] && ((${#INPUTS[@]} > MAX_INPUTS)); then
  INPUTS=("${INPUTS[@]:0:MAX_INPUTS}")
fi
((${#INPUTS[@]} > 0)) || { echo "语料目录中没有可回放文件" >&2; exit 2; }

# 删除旧 gcov 计数后，所有回放只运行独立的 gcov 安装版服务端。
find "${SOURCE_DIR}" -type f -name '*.gcda' -delete
printf 'queue_root=%s\nqueue_dir=%s\ninput_count=%s\nserver_prefix=%s\n' \
  "${QUEUE_ROOT}" "${QUEUE_DIR}" "${#INPUTS[@]}" "${PREFIX}" \
  > "${OUTDIR}/coverage-parameters.txt"

index=0
for seed in "${INPUTS[@]}"; do
  index=$((index + 1))
  run_dir=$(printf '%s/replay-log/%06d' "${OUTDIR}" "${index}")
  mkdir -p "${run_dir}"
  echo "[$index/${#INPUTS[@]}] gcov 回放：$(basename "${seed}")"
  set +e
  python3 /workspace/seed_replay.py "${seed}" "${run_dir}" \
    --repeat 1 --variant gcov > "${run_dir}/replay.log" 2>&1
  status=$?
  set -e
  printf '%s\n' "${status}" > "${run_dir}/exit-status.txt"
done

if ! (
  cd "${SOURCE_DIR}"
  gcovr --root . --object-directory . \
    --filter 'src/(imap-login|imap|lib-imap)/.*' --branches \
    --json -o "${OUTDIR}/gcovr-imap.json"
) > "${OUTDIR}/gcovr.log" 2>&1; then
  tail -n 80 "${OUTDIR}/gcovr.log" >&2
  exit 1
fi
printf 'gcovr 行/分支汇总已生成：%s\n' "${OUTDIR}/gcovr-imap.json"

# gcovr 4.2 的 JSON 不含函数摘要，单独用 gcov 对核心 IMAP 源文件生成函数级数据。
FUNCTION_LOG=${OUTDIR}/gcov-functions.log
KEY_FILES=(
  src/imap-login/imap-login-client.c
  src/imap/imap-commands.c
  src/imap/imap-client.c
  src/imap/cmd-append.c
  src/imap/cmd-fetch.c
  src/imap/cmd-search.c
  src/imap/cmd-select.c
)
: > "${FUNCTION_LOG}"
for relative_source in "${KEY_FILES[@]}"; do
  source_file=${SOURCE_DIR}/${relative_source}
  source_dir=$(dirname "${source_file}")
  source_name=$(basename "${source_file}")
  if [[ -f ${source_dir}/${source_name%.c}.gcno ]]; then
    printf '### gcov-source=%s\n' "${relative_source}" >> "${FUNCTION_LOG}"
    (cd "${source_dir}" && gcov -f -b -c -o . "${source_name}") \
      >> "${FUNCTION_LOG}" 2>&1
  else
    printf '### gcov-source-missing=%s\n' "${relative_source}" >> "${FUNCTION_LOG}"
  fi
done
python3 /workspace/coverage_run.py "${OUTDIR}/gcovr-imap.json" \
  "${OUTDIR}/replay-log" "${OUTDIR}" "${FUNCTION_LOG}"
echo "完成：gcov 独立回放 ${#INPUTS[@]} 个输入，报告位于 ${OUTDIR}"
