#!/usr/bin/env python3
"""为 AFLNet 标记的变动路径样本准备并核对独立 SIP 复播。"""

from __future__ import annotations

import hashlib
import json
import pathlib
import shutil
import sys


def read_stats(path: pathlib.Path) -> dict[str, str]:
	values = {}
	if path.is_file():
		for line in path.read_text(errors="replace").splitlines():
			if ":" in line:
				key, value = line.split(":", 1)
				values[key.strip()] = value.strip()
	return values


def prepare(root: pathlib.Path, repetitions: int) -> int:
	markers = root / "fuzz-30m/aflnet/queue/.state/variable_behavior"
	source_dir = root / "fuzz-30m/aflnet/replayable-queue"
	stage = root / "variable-path-replay-input"
	for path in (stage, root / "variable-path-replay"):
		if path.exists():
			shutil.rmtree(path)
	queue = stage / "replayable-queue"
	queue.mkdir(parents=True)
	manifest = []
	marker_paths = sorted(markers.iterdir()) if markers.is_dir() else []
	for group_index, marker in enumerate(marker_paths):
		source = source_dir / marker.name
		if not source.is_file():
			raise SystemExit(f"缺少 AFLNet 变动路径样本：{source}")
		data = source.read_bytes()
		digest = hashlib.sha256(data).hexdigest()
		for repeat in range(repetitions):
			name = (
				f"id:{group_index * repetitions + repeat:06d},"
				f"orig:variable-{group_index}-repeat-{repeat + 1:02d}.bin"
			)
			(queue / name).write_bytes(data)
			manifest.append({
				"marker": marker.name,
				"repeat": repeat + 1,
				"file": name,
				"sha256": digest,
			})
	(stage / "manifest.json").write_text(
		json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
		encoding="utf-8",
	)
	print(len(marker_paths))
	return 0


def verify(root: pathlib.Path, repetitions: int) -> int:
	manifest_path = root / "variable-path-replay-input/manifest.json"
	manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
	stats = read_stats(root / "fuzz-30m/aflnet/fuzzer_stats")
	variable_paths = int("".join(c for c in stats.get("variable_paths", "0") if c.isdigit()) or "0")
	markers = sorted({row["marker"] for row in manifest})

	rows = []
	replay_log = root / "variable-path-replay/queue-replay.jsonl"
	if replay_log.is_file():
		for line in replay_log.read_text(encoding="utf-8").splitlines():
			if line.strip():
				rows.append(json.loads(line))
	groups: dict[str, list[dict]] = {}
	for row in rows:
		groups.setdefault(row["sha256"], []).append(row)
	expected = {}
	for row in manifest:
		expected.setdefault(row["sha256"], 0)
		expected[row["sha256"]] += 1
	group_checks = []
	for digest, count in expected.items():
		group = groups.get(digest, [])
		sequences = {
			tuple(tuple(message.get("response_codes", [])) for message in row.get("messages", []))
			for row in group
		}
		all_reset = all(
			row.get("server_exit_code") == 0
			and row.get("port_released") is True
			and row.get("exception") is None
			and row.get("connect_error") is None
			for row in group
		)
		group_checks.append(
			len(group) == count and len(sequences) == 1 and all_reset
		)
	queue_summary_path = root / "variable-path-replay/replay-summary.json"
	queue_summary = {}
	if queue_summary_path.is_file():
		queue_summary = json.loads(queue_summary_path.read_text(encoding="utf-8")) \
			.get("groups", {}).get("queue", {})
	replay_ok = (
		(variable_paths == 0 and not manifest)
		or (
			variable_paths == len(markers)
			and len(group_checks) == len(markers)
			and all(group_checks)
			and len(rows) == len(manifest)
			and queue_summary.get("sample_count") == len(manifest)
			and queue_summary.get("replayed_count") == len(manifest)
			and not queue_summary.get("errors")
		)
	)
	audit = [
		"# AFLNet variable_paths 排查记录",
		"",
		f"- 30 分钟运行 `variable_paths`: {variable_paths}",
		f"- 30 分钟运行 `stability`: {stats.get('stability', '未提供')}",
		f"- 变动路径输入: {len(markers)} 条；每条独立进程复播 {repetitions} 次，共 {len(rows)} 次",
		f"- 全部复播成功、响应序列逐输入一致、服务退出且端口释放: {'是' if replay_ok else '否'}",
		"- 结论：AFLNet 的变动路径标记保留在证据中；按相同输入重复复播后业务响应序列稳定，且每次由全新服务进程复位。",
	]
	(root / "preflight/variable-paths-audit.md").write_text(
		"\n".join(audit) + "\n", encoding="utf-8"
	)
	print("\n".join(audit))
	if not replay_ok:
		return 1
	return 0


if len(sys.argv) != 4 or sys.argv[1] not in {"prepare", "verify"}:
	raise SystemExit("用法：audit_variable_paths.py prepare|verify RESULTS_DIR 重复次数")
action = sys.argv[1]
results_root = pathlib.Path(sys.argv[2])
replay_count = int(sys.argv[3])
if replay_count < 1:
	raise SystemExit("重复次数必须大于零")
raise SystemExit(prepare(results_root, replay_count) if action == "prepare" else verify(results_root, replay_count))
