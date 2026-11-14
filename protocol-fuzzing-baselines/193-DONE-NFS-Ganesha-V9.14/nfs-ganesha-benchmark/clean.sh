#!/usr/bin/env bash
set -euo pipefail

# 每条 AFLNet 用例都会重新启动独立的 Ganesha 进程，FSAL_MEM 随进程退出清空。
# AFLNet 在目标进程启动后调用 -c 清理钩子，因此这里不再启动或重置服务。
exit 0
