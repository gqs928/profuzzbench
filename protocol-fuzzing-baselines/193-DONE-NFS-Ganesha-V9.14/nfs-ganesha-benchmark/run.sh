#!/usr/bin/env bash
set -euo pipefail

SECONDS_TO_RUN=${1:-1800}
SEED_DIR=${2:-/results/seeds}
OUTPUT_DIR=${3:-/results/fuzz-run}
mkdir -p "$OUTPUT_DIR"
export GANESHA_LOG="$OUTPUT_DIR/ganesha-critical.log"

if [[ ! -d "$SEED_DIR" ]] || ! compgen -G "$SEED_DIR/*.bin" >/dev/null; then
	python3 /workspace/prepare_seeds.py "$SEED_DIR" "$OUTPUT_DIR/seeds-manifest.json"
else
	cp "$SEED_DIR"/../seeds-manifest.json "$OUTPUT_DIR/seeds-manifest.json" 2>/dev/null || true
fi

FUZZ_DIR="$OUTPUT_DIR/aflnet"
INPUT_SEED_DIR="$OUTPUT_DIR/input-seeds"
mkdir -p "$INPUT_SEED_DIR"
find "$INPUT_SEED_DIR" -maxdepth 1 -type f -name '*.bin' -delete
python3 - "$SEED_DIR" "$INPUT_SEED_DIR" "$OUTPUT_DIR/input-seeds.json" <<'PY'
import hashlib
import json
import pathlib
import shutil
import sys

source = pathlib.Path(sys.argv[1])
destination = pathlib.Path(sys.argv[2])
manifest_path = pathlib.Path(sys.argv[3])
files = []
excluded = {"mount-root.bin"}
for item in sorted(source.glob("*.bin")):
    if item.name in excluded:
        continue
    target = destination / item.name
    shutil.copyfile(item, target)
    files.append({
        "name": item.name,
        "bytes": item.stat().st_size,
        "sha256": hashlib.sha256(item.read_bytes()).hexdigest(),
    })
if not files:
    raise SystemExit(f"AFLNet 有效初始种子为空：{source}")
manifest_path.write_text(
    json.dumps({
        "source_directory": str(source),
        "fuzzable_seed_count": len(files),
        "excluded_initial_seeds": sorted(excluded & {p.name for p in source.glob("*.bin")}),
        "fuzzable_seeds": files,
    }, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
print(f"AFLNet NFS 初始语料 {len(files)} 个；MOUNTv3 种子独立回放和计覆盖")
PY
FUZZ_ARGS=(
	-i "$INPUT_SEED_DIR" -o "$FUZZ_DIR" -t 1000+
	-m none -N tcp://127.0.0.1/12049 -P NFS -D 100000
	-q 3 -s 3 -E -K -R -c /workspace/clean.sh
)
# AFLNet 要求目标是 ELF 文件；这里直接启动固定位于 AFL 插桩前缀的服务程序。
export LD_LIBRARY_PATH="$GANESHA_AFL_PREFIX/lib:$GANESHA_AFL_PREFIX/lib64:$GANESHA_AFL_PREFIX/lib/ganesha:$GANESHA_AFL_PREFIX/lib/x86_64-linux-gnu:$GANESHA_AFL_PREFIX/lib/x86_64-linux-gnu/ganesha"
TARGET=(
	"$GANESHA_AFL_BIN" -F -f "$GANESHA_AFL_CONFIG" -p /tmp/ganesha.pid
	-L "$GANESHA_LOG" -N NIV_CRIT
)
mkdir -p "$FUZZ_DIR"
python3 /workspace/fuzz_supervisor.py \
	"$SECONDS_TO_RUN" "$FUZZ_DIR" "${FUZZ_ARGS[@]}" "${TARGET[@]}" \
	| tee "$OUTPUT_DIR/supervisor.log"

cp "$OUTPUT_DIR/aflnet.log" "$FUZZ_DIR/aflnet.log"
if [[ -f "$FUZZ_DIR/fuzzer_stats" ]]; then
	cp "$FUZZ_DIR/fuzzer_stats" "$OUTPUT_DIR/fuzzer_stats"
fi
if [[ -f "$FUZZ_DIR/ipsm.dot" ]]; then
	cp "$FUZZ_DIR/ipsm.dot" "$OUTPUT_DIR/ipsm.dot"
fi
if [[ -d "$FUZZ_DIR/queue" ]]; then
	find "$FUZZ_DIR/queue" -maxdepth 1 -type f -printf '%f\t%s\n' | sort \
		> "$OUTPUT_DIR/queue-index.tsv"
fi
if [[ -d "$FUZZ_DIR/replayable-crashes" ]]; then
	find "$FUZZ_DIR/replayable-crashes" -maxdepth 1 -type f -printf '%f\t%s\n' | sort \
		> "$OUTPUT_DIR/crash-index.tsv"
fi
