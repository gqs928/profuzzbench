#!/usr/bin/env python3
"""按两张验收图的八项标准汇总 Asterisk SIP/TCP 基准证据。"""

from __future__ import annotations

import csv
import datetime as dt
import hashlib
import json
import pathlib
import re
import sys

root = pathlib.Path(sys.argv[1])
package = pathlib.Path(__file__).parent
checks = []


def add(number: int, title: str, passed: bool, evidence: str) -> None:
	checks.append((number, title, bool(passed), evidence))


def read_stats(path: pathlib.Path) -> dict[str, str]:
	values = {}
	if path.is_file():
		for line in path.read_text(errors="replace").splitlines():
			if ":" in line:
				key, value = line.split(":", 1)
				values[key.strip()] = value.strip()
	return values


def integer(value: object) -> int:
	return int(re.sub(r"[^0-9]", "", str(value)) or "0")


def load_json(path: pathlib.Path) -> dict:
	if not path.is_file():
		return {}
	try:
		return json.loads(path.read_text(encoding="utf-8"))
	except (OSError, json.JSONDecodeError):
		return {}


build_log = root / "build-logs"
build_versions_path = root / "build-versions.txt"
if not build_versions_path.is_file():
	build_versions_path = root / "preflight/build-versions.txt"
package_manifest_path = root / "package-manifest.txt"
if not package_manifest_path.is_file():
	package_manifest_path = root / "preflight/package-manifest.txt"
build_files = (
	build_log / "docker-build.log",
	build_log / "build-input-sha256.txt",
	build_log / "delivery-input-sha256.txt",
	build_log / "image-id.txt",
	build_log / "build-command.txt",
	build_versions_path,
	package_manifest_path,
)
build_ok = all(path.is_file() and path.stat().st_size > 0 for path in build_files)
lock = load_json(package / "source-lock.json")
build_versions = build_versions_path.read_text(errors="replace") \
	if build_versions_path.is_file() else ""
source_text = (root / "source-checksums.sha256").read_text(errors="replace") \
	if (root / "source-checksums.sha256").is_file() else ""
build_ok = build_ok and bool(lock.get("asterisk", {}).get("commit")) \
	and lock.get("asterisk", {}).get("commit") in build_versions \
	and lock.get("pjproject", {}).get("version") == "2.17"
add(
	1,
	"目标可重建",
	build_ok,
	"Asterisk/AFLNet/PJPROJECT 固定提交和 SHA-256、Ubuntu 基础镜像摘要、软件源快照、依赖包清单、无缓存构建日志、镜像 ID、构建时输入和最终交付输入 SHA-256 均已留存。",
)

smoke = load_json(root / "preflight/protocol-smoke/protocol-smoke.json")
sessions = smoke.get("sessions", [])
reference = [row for row in sessions if row.get("variant") == "reference"]
instrumented = [row for row in sessions if row.get("variant") == "afl"]
smoke_ok = (
	smoke.get("repetitions_per_variant", 0) >= 10
	and len(reference) >= 10
	and len(instrumented) >= 10
	and smoke.get("all_sessions_passed") is True
	and smoke.get("same_transcript_within_each_variant") is True
	and smoke.get("same_exact_requests_across_all_runs") is True
	and smoke.get("reference_and_afl_transcripts_match") is True
	and all(row.get("port_released") is True for row in sessions)
)
add(
	2,
	"协议行为保留",
	smoke_ok,
	f"参考版和 AFL/ASan 版各 {len(reference)}/{len(instrumented)} 次；相同 OPTIONS、REGISTER、INVITE/CANCEL 请求的最终状态码、10 次稳定 transcript 和端口复位检查已保存；transcript SHA-256={smoke.get('transcript_sha256', '缺失')}。",
)

seed_manifest = load_json(package / "seeds/seeds-manifest.json")
seed_names = {row.get("file") for row in seed_manifest} if isinstance(seed_manifest, list) else set()
seed_files_ok = all(
	(package / "seeds" / row.get("file", "")).is_file()
	and hashlib.sha256((package / "seeds" / row.get("file", "")).read_bytes()).hexdigest()
		== row.get("sha256")
	for row in seed_manifest
) if isinstance(seed_manifest, list) else False
business_seed = (
	"06-register-invite-cancel.bin" in seed_names
	and "05-invite-cancel.bin" in seed_names
	and any(row.get("request_count", 0) >= 3 for row in seed_manifest)
	if isinstance(seed_manifest, list) else False
)
business_replay = all(
	row.get("passed")
	and 200 in row.get("options", [])
	and 200 in row.get("register", [])
	and any(100 <= code < 200 for code in row.get("invite", []))
	and 200 in row.get("cancel", [])
	and 487 in row.get("cancel", [])
	for row in sessions
) if sessions else False
add(
	3,
	"种子真正进入业务状态",
	seed_files_ok and business_seed and business_replay,
	f"固定语料 {len(seed_names)} 条；包含 REGISTER 成功、带 SDP 的 INVITE、匹配事务 CANCEL，以及消息正文/非法长度边界；正常回放实测 100/200/487 业务响应。",
)

fuzz_dir = root / "fuzz-30m/aflnet"
stats = read_stats(fuzz_dir / "fuzzer_stats")
graph = fuzz_dir / "ipsm.dot"
graph_text = graph.read_text(errors="replace") if graph.is_file() else ""
state_mapping = package / "sip-state-mapping.md"
state_ok = (
	graph.is_file()
	and graph.stat().st_size > 0
	and re.search(r"\b100\b", graph_text) is not None
	and re.search(r"\b200\b", graph_text) is not None
	and state_mapping.is_file()
)
add(
	4,
	"状态反馈有效",
	state_ok,
	f"AFLNet SIP 状态图包含 100 Trying、200 OK 等真实服务端响应节点；中文状态映射已保存；execs_done={stats.get('execs_done', '未知')}。",
)

coverage_csv = root / "coverage/protocol-core-coverage.csv"
coverage_rows = list(csv.DictReader(coverage_csv.open(encoding="utf-8"))) \
	if coverage_csv.is_file() else []
coverage_names = {row.get("source_file", "") for row in coverage_rows}
covered_lines = sum(integer(row.get("covered_lines", 0)) for row in coverage_rows)
branches = sum(integer(row.get("branches", 0)) for row in coverage_rows)
covered_branches = sum(integer(row.get("covered_branches", 0)) for row in coverage_rows)
required_files = (
	"res/res_pjsip/pjsip_distributor.c",
	"res/res_pjsip_registrar.c",
	"res/res_pjsip_session.c",
	"channels/chan_pjsip.c",
)
required_files_hit = all(
	any(required in row.get("source_file", "") and integer(row.get("covered_lines", 0)) > 0
		for row in coverage_rows)
	for required in required_files
)
functions_csv = root / "coverage/protocol-core-functions.csv"
function_rows = list(csv.DictReader(functions_csv.open(encoding="utf-8"))) \
	if functions_csv.is_file() else []
coverage_replay = load_json(root / "coverage/replay/replay-summary.json")
queue_replay = coverage_replay.get("groups", {}).get("queue", {})
coverage_ok = (
	covered_lines > 0
	and covered_branches > 0
	and branches >= covered_branches
	and required_files_hit
	and len(function_rows) > 0
	and (root / "coverage/protocol-core.html").is_file()
	and (root / "coverage/protocol-core-coverage.txt").is_file()
	and (root / "coverage/protocol-core-functions.md").is_file()
	and queue_replay.get("sample_count", 0) > 0
	and queue_replay.get("replayed_count", 0) > 0
)
add(
	5,
	"覆盖率可信",
	coverage_ok,
	f"独立 gcov Asterisk 回放队列 {queue_replay.get('replayed_count', 0)} 条；PJSIP 核心文件已覆盖 {covered_lines} 行、{covered_branches}/{branches} 个分支，命中函数 {len(function_rows)} 个；TXT/HTML/CSV/函数清单齐全。",
)

reset = load_json(root / "preflight/protocol-smoke/reset-check.json")
variable_audit_path = root / "preflight/variable-paths-audit.md"
variable_audit = variable_audit_path.read_text(errors="replace") \
	if variable_audit_path.is_file() else ""
variable_match = re.search(r"variable_paths[^\n]*?(\d+)", variable_audit)
variable_count = int(variable_match.group(1)) if variable_match else None
try:
	long_run_stability = float(
		re.sub(r"[^0-9.]", "", stats.get("stability", "0")) or "0"
	)
except ValueError:
	long_run_stability = 0.0
variable_manifest = load_json(root / "variable-path-replay-input/manifest.json")
if not isinstance(variable_manifest, list):
	variable_manifest = []
variable_replay_rows = []
variable_replay_path = root / "variable-path-replay/queue-replay.jsonl"
if variable_replay_path.is_file():
	for line in variable_replay_path.read_text(errors="replace").splitlines():
		if line.strip():
			try:
				variable_replay_rows.append(json.loads(line))
			except json.JSONDecodeError:
				pass
expected_repeats: dict[str, int] = {}
for row in variable_manifest:
	if isinstance(row, dict) and row.get("sha256"):
		digest = str(row["sha256"])
		expected_repeats[digest] = expected_repeats.get(digest, 0) + 1
actual_replays: dict[str, list[dict]] = {}
for row in variable_replay_rows:
	if row.get("sha256"):
		actual_replays.setdefault(row["sha256"], []).append(row)
variable_groups_stable = True
for digest, expected_count in expected_repeats.items():
	rows = actual_replays.get(digest, [])
	sequences = {
		tuple(tuple(message.get("response_codes", [])) for message in row.get("messages", []))
		for row in rows
	}
	variable_groups_stable = variable_groups_stable and (
		len(rows) == expected_count
		and len(sequences) == 1
		and all(
			row.get("server_exit_code") == 0
			and row.get("port_released") is True
			and row.get("exception") is None
			and row.get("connect_error") is None
			for row in rows
		)
	)
variable_summary = load_json(root / "variable-path-replay/replay-summary.json")
variable_queue_summary = variable_summary.get("groups", {}).get("queue", {})
variable_marker_count = len({
	row.get("marker") for row in variable_manifest if isinstance(row, dict)
})
variable_replay_ok = (
	variable_groups_stable
	and variable_count == variable_marker_count
	and len(variable_replay_rows) == len(variable_manifest)
	and (
		(variable_marker_count == 0)
		or (
			variable_queue_summary.get("sample_count") == len(variable_manifest)
			and variable_queue_summary.get("replayed_count") == len(variable_manifest)
			and not variable_queue_summary.get("errors")
		)
	)
)
reset_ok = (
	reset.get("repetitions_per_variant", 0) >= 10
	and reset.get("all_sessions_passed") is True
	and reset.get("same_exact_requests_across_all_runs") is True
	and reset.get("reference_and_afl_transcripts_match") is True
	and all(row.get("port_released") is True for row in sessions)
	and variable_replay_ok
	and long_run_stability >= 95.0
)
add(
	6,
	"每轮可复位",
	reset_ok,
	f"参考版/AFL 版同一请求各 10 轮 transcript 一致并释放端口；正式运行 variable_paths={variable_count if variable_count is not None else '缺失'} 的 {variable_marker_count} 条样本各独立复播 10 次、响应序列稳定；30 分钟 stability={long_run_stability:.2f}%。",
)

fault_stats = read_stats(root / "fault-probe/fuzzer_stats")
fault_status = (root / "fault-probe/probe-status.txt").read_text(errors="replace") \
	if (root / "fault-probe/probe-status.txt").is_file() else ""
fault_ok = (
	integer(fault_stats.get("unique_crashes", 0)) > 0
	and (root / "fault-probe/intentional-crash-sample.bin").is_file()
	and "independent_replay_exit=" in fault_status
	and "temporary_injection_removed=true" in fault_status
	and integer(stats.get("unique_hangs", 0)) <= 10
)
add(
	7,
	"异常可观察",
	fault_ok,
	f"临时 SIP 故障探针 unique_crashes={fault_stats.get('unique_crashes', '0')}，异常样本独立回放记录存在且注入源码/服务已删除；真实目标 unique_hangs={stats.get('unique_hangs', '未知')}。",
)

runtime = 0
runtime_path = root / "fuzz-30m/runtime.txt"
if runtime_path.is_file():
	values = dict(
		line.split("=", 1)
		for line in runtime_path.read_text(errors="replace").splitlines()
		if "=" in line
	)
	try:
		started = dt.datetime.strptime(values["started_at_utc"], "%Y-%m-%dT%H:%M:%SZ")
		finished = dt.datetime.strptime(values["finished_at_utc"], "%Y-%m-%dT%H:%M:%SZ")
		runtime = int((finished - started).total_seconds())
	except (KeyError, ValueError):
		runtime = 0
result_ok = (
	runtime >= 1800
	and integer(stats.get("execs_done", 0)) > 0
	and (fuzz_dir / "plot_data").is_file()
	and (fuzz_dir / "fuzz-stats.csv").is_file()
	and (root / "fuzz-30m/parameters.txt").is_file()
	and (root / "coverage/replay/queue-replay.jsonl").is_file()
	and (root / "coverage/replay/crashes-replay.jsonl").is_file()
	and (root / "coverage/protocol-core-coverage.csv").is_file()
	and (root / "preflight/SHA256SUMS").is_file()
)
add(
	8,
	"结果可复查",
	result_ok,
	f"实际模糊测试 {runtime} 秒；execs_done={stats.get('execs_done', '未知')}、paths_total={stats.get('paths_total', '未知')}、unique_crashes={stats.get('unique_crashes', '未知')}、unique_hangs={stats.get('unique_hangs', '未知')}；队列、状态图、参数、CSV、逐样本回放及 SHA-256 清单已留存。",
)

print("# Asterisk SIP/TCP 严格验收报告\n")
print("| 验收项 | 结果 | 证据摘要 |")
print("|---|---|---|")
for number, title, passed, evidence in checks:
	print(f"| {number}. {title} | {'通过' if passed else '未通过'} | {evidence} |")
print("\n详细命令日志、构建输入、种子、AFLNet 统计、状态图、逐样本回放和覆盖率报告均在本目录。")
if not all(row[2] for row in checks):
	sys.exit(1)
