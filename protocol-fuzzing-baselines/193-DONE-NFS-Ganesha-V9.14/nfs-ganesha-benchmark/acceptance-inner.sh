#!/usr/bin/env bash
set -euo pipefail

FUZZ_SECONDS=${1:-1800}
if ((FUZZ_SECONDS < 1800)); then
	echo "完整验收要求 AFLNet 连续运行至少 1800 秒" >&2
	exit 2
fi

RESULTS=/results
mkdir -p "$RESULTS"
(cd /workspace && sha256sum -c source/SHA256SUMS) \
	| tee "$RESULTS/source-checksums.log"
python3 /workspace/protocol_smoke.py "$RESULTS/protocol-smoke" 10 \
	| tee "$RESULTS/protocol-smoke.log"
python3 /workspace/prepare_seeds.py "$RESULTS/seeds" "$RESULTS/seeds-manifest.json" \
	| tee "$RESULTS/prepare-seeds.log"
python3 /workspace/seed_replay.py "$RESULTS/seeds" "$RESULTS/seed-replay" 10 reference \
	| tee "$RESULTS/seed-replay.log"
/workspace/run.sh "$FUZZ_SECONDS" "$RESULTS/seeds" "$RESULTS/fuzz"
python3 /workspace/fuzz_report.py "$RESULTS/fuzz"
python3 /workspace/coverage_replay.py "$RESULTS/seeds" "$RESULTS/fuzz/aflnet" "$RESULTS/coverage" 3 \
	| tee "$RESULTS/coverage-replay.log"
python3 /workspace/ganesha_anomaly_replay.py "$RESULTS/fuzz/aflnet" "$RESULTS/ganesha-anomaly-replay" 10 \
	| tee "$RESULTS/ganesha-anomaly-replay.log"

mkdir -p "$RESULTS/fault-probe/seeds"
python3 /workspace/fault_probe.py "$RESULTS/fault-probe/seeds"
# 探针处理一次请求后会自行退出；不加 -K，避免发送 SIGTERM 遮蔽目标的 SIGABRT。
set +e
timeout --signal=INT --kill-after=5s 60s \
	/home/ubuntu/aflnet/afl-fuzz \
	-i "$RESULTS/fault-probe/seeds" -o "$RESULTS/fault-probe/aflnet" \
	-N tcp://127.0.0.1/12059 -P NFS -D 100000 -E -R -t 3000 \
	/home/ubuntu/experiments/fault-probe 12059 \
	> "$RESULTS/fault-probe/aflnet.log" 2>&1
fuzz_status=$?
set -e
if [[ $fuzz_status -ne 0 && $fuzz_status -ne 124 && $fuzz_status -ne 130 ]]; then
	cat "$RESULTS/fault-probe/aflnet.log"
	exit "$fuzz_status"
fi

crash_sample=$(find "$RESULTS/fault-probe/aflnet/replayable-crashes" -maxdepth 1 -type f \
	! -name README.txt -print -quit 2>/dev/null || true)
if [[ -z "$crash_sample" ]]; then
	echo "AFLNet 故障探针运行未记录 replayable-crashes 样本" >&2
	cat "$RESULTS/fault-probe/aflnet.log"
	exit 1
fi
python3 /workspace/fault_probe_replay.py "$crash_sample" "$RESULTS/fault-probe/replay"

cp /home/ubuntu/experiments/build-versions.txt "$RESULTS/build-versions.txt"
cp /workspace/source/SHA256SUMS "$RESULTS/source-SHA256SUMS.txt"
python3 - "$RESULTS" <<'PY'
import hashlib
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
items = []
for path in sorted(root.rglob("*")):
    if path.is_file() and path.name != "evidence-manifest.json":
        items.append({
            "path": str(path.relative_to(root)),
            "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        })
(root / "evidence-manifest.json").write_text(
    json.dumps({"files": items}, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
print(f"已保存 {len(items)} 个验收证据及 SHA-256 清单")
PY
echo "完整验收通过；证据保存在 $RESULTS"
