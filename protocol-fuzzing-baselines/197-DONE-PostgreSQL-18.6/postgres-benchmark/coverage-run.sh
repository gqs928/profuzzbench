#!/usr/bin/env bash
set -euo pipefail

# 用法：coverage-run.sh AFL 输出目录 崩溃样本目录 挂起样本目录
FUZZ_DIR=${1:?用法：coverage-run.sh AFL输出 崩溃目录 挂起目录}
OUTDIR=${2:?用法：coverage-run.sh AFL输出 崩溃目录 挂起目录}
CRASHES=${3:-}
HANGS=${4:-}
SOURCE=${POSTGRES_GCOV_SOURCE:-/home/ubuntu/experiments/src-gcov}
TARGET=${POSTGRES_GCOV_BIN:-/home/ubuntu/experiments/postgres-gcov/bin/postgres}
INITDB=${POSTGRES_INITDB_BIN:-/home/ubuntu/experiments/postgres-reference/bin/initdb}
PG_CTL=${POSTGRES_PG_CTL_BIN:-/home/ubuntu/experiments/postgres-reference/bin/pg_ctl}
PG_ISREADY=${POSTGRES_PG_ISREADY_BIN:-/home/ubuntu/experiments/postgres-reference/bin/pg_isready}

[[ -d ${FUZZ_DIR}/queue ]] || { echo "AFL 队列目录不存在：${FUZZ_DIR}/queue" >&2; exit 2; }
[[ -x ${TARGET} && -x ${INITDB} && -x ${PG_CTL} && -x ${PG_ISREADY} ]] || {
	echo "gcov PostgreSQL 或复位工具不存在。" >&2
	exit 2
}
if [[ -e ${OUTDIR} ]] && [[ -n $(find "${OUTDIR}" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null) ]]; then
	echo "覆盖率输出目录非空：${OUTDIR}" >&2
	exit 2
fi
mkdir -p "${OUTDIR}"
cat > "${OUTDIR}/coverage-parameters.txt" <<EOF
instrumentation=GCC gcov (--coverage)
target=${TARGET}
source=${SOURCE}
queue=${FUZZ_DIR}/queue
crashes=${CRASHES}
hangs=${HANGS}
each_sample_uses_fresh_cluster=true
core_files=src/backend/tcop/postgres.c,src/backend/libpq/pqcomm.c,src/backend/libpq/auth.c,src/backend/libpq/pqformat.c
EOF
find "${SOURCE}" -type f -name '*.gcda' -delete
ARGS=(--queue "${FUZZ_DIR}/queue" --output "${OUTDIR}/replay"
	--postgres "${TARGET}" --initdb "${INITDB}" --pg-ctl "${PG_CTL}"
	--pg-isready "${PG_ISREADY}" --port 5432)
if [[ -n ${CRASHES} && -d ${CRASHES} ]]; then ARGS+=(--crashes "${CRASHES}"); fi
if [[ -n ${HANGS} && -d ${HANGS} ]]; then ARGS+=(--crashes "${HANGS}"); fi
python3 /workspace/coverage_replay.py "${ARGS[@]}" \
	| tee "${OUTDIR}/replay.log"

mkdir -p "${OUTDIR}/coverage"
mkdir -p "${OUTDIR}/coverage/gcovr-parts"
(
	cd "${SOURCE}/src/backend/tcop"
	gcov -b -c -f -o . postgres.c \
		> "${OUTDIR}/coverage/gcovr-parts/tcop-gcov.txt"
	gcovr --root "${SOURCE}" --object-directory . --filter='.*postgres\.c$' --branches \
		--print-summary --output "${OUTDIR}/coverage/gcovr-parts/tcop.txt"
	gcovr --root "${SOURCE}" --object-directory . --filter='.*postgres\.c$' --branches \
		--html-details "${OUTDIR}/coverage/gcovr-parts/tcop.html"
	gcovr --root "${SOURCE}" --object-directory . --filter='.*postgres\.c$' --branches \
		--json-pretty --output "${OUTDIR}/coverage/gcovr-parts/tcop.json"
)
(
	cd "${SOURCE}/src/backend/libpq"
	gcov -b -c -f -o . pqcomm.c auth.c pqformat.c \
		> "${OUTDIR}/coverage/gcovr-parts/libpq-gcov.txt"
	gcovr --root "${SOURCE}" --object-directory . \
		--filter='.*(pqcomm|auth|pqformat)\.c$' --branches \
		--print-summary --output "${OUTDIR}/coverage/gcovr-parts/libpq.txt"
	gcovr --root "${SOURCE}" --object-directory . \
		--filter='.*(pqcomm|auth|pqformat)\.c$' --branches \
		--html-details "${OUTDIR}/coverage/gcovr-parts/libpq.html"
	gcovr --root "${SOURCE}" --object-directory . \
		--filter='.*(pqcomm|auth|pqformat)\.c$' --branches \
		--json-pretty --output "${OUTDIR}/coverage/gcovr-parts/libpq.json"
)
cat "${OUTDIR}/coverage/gcovr-parts/tcop.txt" \
	"${OUTDIR}/coverage/gcovr-parts/libpq.txt" \
	> "${OUTDIR}/coverage/protocol-core-coverage.txt"
cat > "${OUTDIR}/coverage/index.html" <<EOF
<!doctype html>
<html lang="zh-CN"><meta charset="utf-8"><title>PostgreSQL 协议核心覆盖率</title>
<h1>PostgreSQL 协议核心覆盖率</h1>
<ul><li><a href="gcovr-parts/tcop.html">tcop/postgres.c</a></li>
<li><a href="gcovr-parts/libpq.html">libpq/pqcomm.c、auth.c、pqformat.c</a></li></ul>
</html>
EOF
python3 - "${OUTDIR}/coverage/gcovr-parts/tcop.json" \
	"${OUTDIR}/coverage/gcovr-parts/libpq.json" \
	"${OUTDIR}/coverage/gcovr-parts/tcop-gcov.txt" \
	"${OUTDIR}/coverage/gcovr-parts/libpq-gcov.txt" \
	"${OUTDIR}/coverage/gcovr.json" <<'PY'
import json
import pathlib
import re
import sys

merged = {"files": [], "gcovr/format_version": 0.1}
canonical = {
	"postgres.c": "src/backend/tcop/postgres.c",
	"pqcomm.c": "src/backend/libpq/pqcomm.c",
	"auth.c": "src/backend/libpq/auth.c",
	"pqformat.c": "src/backend/libpq/pqformat.c",
}
for part in sys.argv[1:3]:
	report = json.loads(pathlib.Path(part).read_text(encoding="utf-8"))
	for item in report.get("files", []):
		name = pathlib.Path(item.get("file", "")).name
		if name in canonical:
			item["file"] = canonical[name]
			merged["files"].append(item)
function_owners = {
	"PostgresMain": "src/backend/tcop/postgres.c",
	"exec_simple_query": "src/backend/tcop/postgres.c",
	"exec_parse_message": "src/backend/tcop/postgres.c",
	"exec_bind_message": "src/backend/tcop/postgres.c",
	"exec_execute_message": "src/backend/tcop/postgres.c",
	"pq_getmessage": "src/backend/libpq/pqcomm.c",
	"ClientAuthentication": "src/backend/libpq/auth.c",
}
for log_path in sys.argv[3:5]:
	lines = pathlib.Path(log_path).read_text(errors="replace").splitlines()
	for index, line in enumerate(lines[:-1]):
		match = re.match(r"Function '([^']+)'", line)
		if not match or match.group(1) not in function_owners:
			continue
		coverage = re.match(r"Lines executed:([0-9.]+)% of (\d+)", lines[index + 1])
		if not coverage:
			continue
		owner = function_owners[match.group(1)]
		for item in merged["files"]:
			if item["file"] == owner:
				item.setdefault("functions", []).append({
					"name": match.group(1),
					"line_coverage_percent": float(coverage.group(1)),
					"instrumented_lines": int(coverage.group(2)),
				})
pathlib.Path(sys.argv[5]).write_text(
	json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY
python3 /workspace/summarize_coverage.py \
	"${OUTDIR}/coverage/gcovr.json" "${OUTDIR}/coverage"
find "${SOURCE}" -type f -name '*.gcda' -printf '%P %s bytes\n' \
	| sort > "${OUTDIR}/gcda-files.txt"
test -s "${OUTDIR}/coverage/protocol-core-coverage.csv"
test -s "${OUTDIR}/coverage/core-function-coverage.csv"
test -s "${OUTDIR}/replay/queue-replay.jsonl"
echo "通过：队列、崩溃和挂起样本已逐条回放；协议核心 gcov 行/分支/函数覆盖率已导出。"
