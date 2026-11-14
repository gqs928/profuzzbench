#!/usr/bin/env bash
set -euo pipefail

PACKAGE_DIR=$(cd "$(dirname "$0")" && pwd)
IMAGE=${1:-asterisk-sip-fuzz}
shift || true
NO_CACHE=()
for option in "$@"; do
	case "$option" in
		--no-cache) NO_CACHE+=(--no-cache) ;;
		*) echo "未知构建参数：$option" >&2; exit 2 ;;
	esac
done

BUILD_LOG_DIR=${BUILD_LOG_DIR:-"${PACKAGE_DIR}/results/build-logs"}
mkdir -p "${BUILD_LOG_DIR}"
chmod +x "${PACKAGE_DIR}"/*.sh

(
	cd "${PACKAGE_DIR}"
	find . -type f ! -path './results/*' ! -name build-input-sha256.txt \
		-print0 | sort -z | xargs -0 sha256sum > "${BUILD_LOG_DIR}/build-input-sha256.txt"
)
{
	printf 'image=%s\n' "${IMAGE}"
	printf 'make_jobs=%s\n' "${ASTERISK_MAKE_JOBS:-2}"
	printf 'no_cache=%s\n' "$([[ ${#NO_CACHE[@]} -gt 0 ]] && echo true || echo false)"
	printf 'build_context=%s\n' "${PACKAGE_DIR}"
} > "${BUILD_LOG_DIR}/build-command.txt"

# 基础镜像引用已锁定到摘要；复用本机同摘要镜像，缺失时 Docker 会自动拉取。
DOCKER_BUILDKIT=1 docker build --progress=plain \
	--build-arg "MAKE_JOBS=${ASTERISK_MAKE_JOBS:-2}" \
	"${NO_CACHE[@]}" -t "${IMAGE}" "${PACKAGE_DIR}" \
	2>&1 | tee "${BUILD_LOG_DIR}/docker-build.log"
docker image inspect --format '{{.Id}}' "${IMAGE}" \
	> "${BUILD_LOG_DIR}/image-id.txt"
echo "镜像构建完成：${IMAGE}；构建记录位于 ${BUILD_LOG_DIR}"
