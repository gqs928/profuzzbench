#!/usr/bin/env bash
set -euo pipefail

OUTDIR=${1:-/results/fault-probe}
WORKDIR=${WORKDIR:-/home/ubuntu/experiments}
SOURCE_DIR=${WORKDIR}/src-afl
PREFIX=${DOVECOT_AFL_PREFIX:-${WORKDIR}/dovecot-afl}
FUZZ_OUT=${OUTDIR}/dovecot-injected-run
TRIGGER_SEEDS=${OUTDIR}/trigger-seeds

if (( EUID != 0 )); then
  echo "Dovecot 故障注入构建需要容器 root 身份" >&2
  exit 2
fi
if [[ -e ${OUTDIR} ]] && [[ -n $(find "${OUTDIR}" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null) ]]; then
  echo "故障注入验收目录非空，请选择新目录：${OUTDIR}" >&2
  exit 2
fi
[[ -f ${SOURCE_DIR}/src/imap-login/client-authenticate.c ]] || { echo "缺少锁定的 AFL Dovecot 源码树" >&2; exit 2; }
[[ -f /workspace/dovecot-fault-injection.patch ]] || { echo "缺少临时故障注入补丁" >&2; exit 2; }
[[ -f /workspace/fault-kill-helper.c ]] || { echo "缺少临时崩溃传播助手源码" >&2; exit 2; }
mkdir -p "${OUTDIR}"
ulimit -c 0

# 限定系统工具路径，避免 AFL 的 as 包装器被助手编译过程递归调用。
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
  cc -O2 -Wall -Wextra -Werror /workspace/fault-kill-helper.c \
  -o /usr/local/bin/dovecot-fault-kill-helper
chown root:root /usr/local/bin/dovecot-fault-kill-helper
chmod 4755 /usr/local/bin/dovecot-fault-kill-helper

SOURCE_FILE=${SOURCE_DIR}/src/imap-login/client-authenticate.c
ORIGINAL_COPY=${OUTDIR}/client-authenticate-source-original.c
INJECTED_COPY=${OUTDIR}/client-authenticate-source-injected.c
cp "${SOURCE_FILE}" "${ORIGINAL_COPY}"
SOURCE_BEFORE=$(sha256sum "${SOURCE_FILE}" | cut -d ' ' -f1)
PATCH_SHA256=$(sha256sum /workspace/dovecot-fault-injection.patch | cut -d ' ' -f1)

patch -d "${SOURCE_DIR}" -p1 < /workspace/dovecot-fault-injection.patch \
  > "${OUTDIR}/patch-apply.log"
cp "${SOURCE_FILE}" "${INJECTED_COPY}"
if ! make -C "${SOURCE_DIR}/src/imap-login" -j2 install \
  > "${OUTDIR}/injected-build.log" 2>&1; then
  tail -n 80 "${OUTDIR}/injected-build.log" >&2
  exit 1
fi

# 撤回源码改动；只有这次容器中的 imap-login 二进制保留验收注入。
patch -R -d "${SOURCE_DIR}" -p1 < /workspace/dovecot-fault-injection.patch \
  > "${OUTDIR}/patch-revert.log"
cmp -s "${SOURCE_FILE}" "${ORIGINAL_COPY}"
SOURCE_AFTER=$(sha256sum "${SOURCE_FILE}" | cut -d ' ' -f1)
BINARY_SHA256=$(sha256sum "${PREFIX}/libexec/dovecot/imap-login" | cut -d ' ' -f1)
INJECTION_MARKER=$(
  strings "${PREFIX}/libexec/dovecot/imap-login" \
    | grep -F -c '/usr/local/bin/dovecot-fault-kill-helper' || true
)
HELPER_SHA256=$(sha256sum /usr/local/bin/dovecot-fault-kill-helper | cut -d ' ' -f1)
printf 'source_sha256_before=%s\nsource_sha256_after=%s\nsource_patch_removed=%s\ninjected_imap_login_binary_sha256=%s\ninjection_marker_count=%s\ninjection_patch_sha256=%s\nfault_helper_sha256=%s\nfault_helper_setuid=%s\n' \
  "${SOURCE_BEFORE}" "${SOURCE_AFTER}" \
  "$([[ ${SOURCE_BEFORE} == "${SOURCE_AFTER}" ]] && echo true || echo false)" \
  "${BINARY_SHA256}" "${INJECTION_MARKER}" "${PATCH_SHA256}" "${HELPER_SHA256}" \
  "$([[ -u /usr/local/bin/dovecot-fault-kill-helper ]] && echo true || echo false)" \
  > "${OUTDIR}/injection-manifest.txt"

export INPUTS=${TRIGGER_SEEDS}
export DICT=/workspace/dovecot-fault.dict
export DOVECOT_AFL_PREFIX=${PREFIX}
export AFL_FAST=0
export IMAP_STARTUP_DELAY=500000
mkdir -p "${TRIGGER_SEEDS}"
# 使用有效的短账号缩短种子；保持 LOGIN 命令正常，仅变异认证字段触发注入。
# 临时探针服务 chroot 到根目录，让登录 worker 能执行容器内的故障助手。
printf 'u:{plain}p\n' > "${OUTDIR}/passwd-fault"
sed "s#passwd_file_path = /workspace/passwd#passwd_file_path = ${OUTDIR}/passwd-fault#" \
  /workspace/dovecot.conf \
  | awk '{ print; if ($0 == "service imap-login {") print "  chroot = /" }' \
  > "${OUTDIR}/dovecot-fault.conf"
chmod a+r "${OUTDIR}/passwd-fault" "${OUTDIR}/dovecot-fault.conf"
export DOVECOT_CONFIG=${OUTDIR}/dovecot-fault.conf
printf 'login_worker_chroot=/\nprobe_config_sha256=%s\n' \
  "$(sha256sum "${DOVECOT_CONFIG}" | cut -d ' ' -f1)" \
  >> "${OUTDIR}/injection-manifest.txt"
printf 'A LOGIN u p\r\n' > "${TRIGGER_SEEDS}/login-tag-mutation.imap"
rm -f /tmp/dovecot-injection.trace
set +e
bash /workspace/run.sh "${FUZZ_OUT}" "${DOVECOT_FAULT_PROBE_DURATION:-30s}" \
  2>&1 | tee "${OUTDIR}/dovecot-fuzz.log"
RUN_STATUS=${PIPESTATUS[0]}
set -e
if [[ -f /tmp/dovecot-injection.trace ]]; then
  cp /tmp/dovecot-injection.trace "${OUTDIR}/dovecot-injection.trace"
fi
if [[ -d /tmp/dovecot-benchmark-state/log ]]; then
  cp -a /tmp/dovecot-benchmark-state/log "${OUTDIR}/dovecot-logs"
fi

STATS=${FUZZ_OUT}/fuzzer_stats
CRASH_DIR=${FUZZ_OUT}/replayable-crashes
[[ -d ${CRASH_DIR} ]] || CRASH_DIR=${FUZZ_OUT}/crashes
CRASH_COUNT=$(find "${CRASH_DIR}" -maxdepth 1 -type f -name 'id:*' 2>/dev/null | wc -l)
UNIQUE_CRASHES=0
if [[ -f ${STATS} ]]; then
  UNIQUE_CRASHES=$(awk -F: '$1 ~ /^unique_crashes[[:space:]]*$/ {gsub(/[[:space:]]/, "", $2); print $2}' "${STATS}")
fi
printf 'fuzzer_exit_status=%s\nunique_crashes=%s\nreplayable_crash_files=%s\n' \
  "${RUN_STATUS}" "${UNIQUE_CRASHES:-0}" "${CRASH_COUNT}" \
  > "${OUTDIR}/fault-probe-result.txt"
chmod -R a+rX "${OUTDIR}"

if (( CRASH_COUNT < 1 )) || (( ${UNIQUE_CRASHES:-0} < 1 )); then
  echo "未在临时故障注入版 Dovecot 上观察到 AFLNet 崩溃样本" >&2
  exit 1
fi
echo "通过：AFLNet 在临时故障注入版 Dovecot 上保存了 ${CRASH_COUNT} 个异常样本；源码改动已撤回，测试二进制与临时助手随容器销毁。"
