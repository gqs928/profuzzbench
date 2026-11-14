#!/usr/bin/env bash
set -euo pipefail

# 用法：coverage-run.sh AFLNET 输出目录 覆盖率目录 [队列上限]
if (($# < 2)); then
	echo "用法：coverage-run.sh AFLNET输出目录 覆盖率目录 [队列上限]" >&2
	exit 2
fi
FUZZ_DIR=$1
OUTDIR=$2
LIMIT=${3:-200}
GCOV_SOURCE=${ASTERISK_GCOV_SOURCE:-/home/ubuntu/asterisk-gcov-source}
FILTER='.*(res/res_pjsip[^/]*\.c|res/res_pjsip/.*\.c|channels/chan_pjsip\.c)$'

if [[ -e ${OUTDIR} ]] && [[ -n $(find "${OUTDIR}" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null) ]]; then
	echo "覆盖率输出目录非空，请使用新目录：${OUTDIR}" >&2
	exit 2
fi
mkdir -p "${OUTDIR}"
find "${GCOV_SOURCE}" -type f -name '*.gcda' -delete
python3 /workspace/coverage_replay.py \
	--fuzz-dir "${FUZZ_DIR}" --output "${OUTDIR}/replay" --limit "${LIMIT}" \
	2>&1 | tee "${OUTDIR}/replay.log"

gcovr --root "${GCOV_SOURCE}" \
	--filter "${FILTER}" --branches \
	--html-details "${OUTDIR}/protocol-core.html" "${GCOV_SOURCE}"
gcovr --root "${GCOV_SOURCE}" \
	--filter "${FILTER}" --branches --json -o "${OUTDIR}/protocol-core.json" \
	"${GCOV_SOURCE}"
gcovr --root "${GCOV_SOURCE}" \
	--filter "${FILTER}" --branches --print-summary "${GCOV_SOURCE}" \
	> "${OUTDIR}/protocol-core-coverage.txt"
python3 /workspace/summarize_coverage.py \
	"${OUTDIR}/protocol-core.json" "${OUTDIR}" "${GCOV_SOURCE}"
(
	cd "${OUTDIR}"
	find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS
)
echo "覆盖率报告：${OUTDIR}/protocol-core.html、protocol-core-coverage.csv 和 protocol-core-functions.md"
