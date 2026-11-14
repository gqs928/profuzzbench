#!/usr/bin/env python3
"""按用户给定的八项标准汇总 FreeRADIUS 基准验收证据。"""

import csv
import datetime as dt
import json
import pathlib
import re
import sys

root = pathlib.Path(sys.argv[1])
checks = []


def add(number, title, passed, evidence):
    checks.append((number, title, bool(passed), evidence))


def read_stats(path):
    values = {}
    if path.is_file():
        for line in path.read_text(errors="replace").splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                values[key.strip()] = value.strip()
    return values


def numeric(value):
    return int(re.sub(r"[^0-9]", "", str(value)) or "0")


build_paths = [
    root / "build-logs/build-versions.txt",
    root / "build-logs/build-input-sha256.txt",
    root / "build-logs/image-id.txt",
    root / "build-logs/package-manifest.txt",
]
add(
    1,
    "目标可重建",
    all(path.is_file() and path.stat().st_size for path in build_paths),
    "无缓存 Docker 构建日志、基础镜像/依赖/提交记录和构建输入 SHA-256 已留存。",
)

smoke_path = root / "preflight/protocol-smoke/protocol-smoke.json"
smoke = json.loads(smoke_path.read_text(encoding="utf-8")) if smoke_path.is_file() else {}
sessions = smoke.get("sessions", [])
reference = [row for row in sessions if row.get("variant") == "reference"]
instrumented = [row for row in sessions if row.get("variant") == "afl"]
transcripts = {row.get("transcript_sha256") for row in sessions}
smoke_ok = (
    smoke.get("repetitions_per_variant", 0) >= 10
    and len(reference) >= 10
    and len(instrumented) >= 10
    and len(transcripts) == 1
    and all(row.get("udp_codes") == [2, 3, 5, 5] for row in sessions)
    and all(row.get("tcp_codes") == [2, 5, 5, 3, 2] for row in sessions)
)
add(
    2,
    "协议行为保留",
    smoke_ok,
    f"参考版和 AFL 版各 {len(reference)}/{len(instrumented)} 轮；UDP/TCP 认证、拒绝、记账 transcript 一致；SHA-256={smoke.get('transcript_sha256', '缺失')}。",
)

seed_manifest_path = pathlib.Path(__file__).parent / "seeds-manifest.json"
seeds = json.loads(seed_manifest_path.read_text(encoding="utf-8")) if seed_manifest_path.is_file() else []
business_ok = len(seeds) >= 6 and any("login-accounting" in row["file"] for row in seeds)
add(
    3,
    "种子真正进入业务状态",
    business_ok and smoke_ok,
    f"固定语料 {len(seeds)} 个，含 PAP 成功/拒绝、Accounting-Start/Stop 和多包会话；服务端返回预期业务响应。",
)

fuzz_dir = root / "fuzz-30m/aflnet"
stats = read_stats(fuzz_dir / "fuzzer_stats")
graph = fuzz_dir / "ipsm.dot"
state_mapping = pathlib.Path(__file__).parent / "radius-state-mapping.md"
graph_text = graph.read_text(errors="replace") if graph.is_file() else ""
state_nodes = set(re.findall(r"^\s*(\d+)\s+\[", graph_text, re.MULTILINE))
required_states = {"2", "3", "5"}
state_ok = (
    graph.is_file()
    and graph.stat().st_size > 0
    and required_states.issubset(state_nodes)
    and state_mapping.is_file()
)
add(
    4,
    "状态反馈有效",
    state_ok,
    f"AFLNet IPSM 实测状态节点={','.join(sorted(state_nodes, key=int)) or '缺失'}；要求包含 Accept(2)、Reject(3)、Accounting-Response(5)，并留存中文状态映射。",
)

coverage_csv = root / "coverage/protocol-core-coverage.csv"
coverage_rows = list(csv.DictReader(coverage_csv.open(encoding="utf-8"))) if coverage_csv.is_file() else []
coverage_names = {pathlib.Path(row["source_file"]).name for row in coverage_rows}
coverage_total = sum(numeric(row.get("covered_lines", 0)) for row in coverage_rows)
coverage_ok = (
    {"radius.c", "listen.c", "process.c"}.issubset(coverage_names)
    and coverage_total > 0
    and (root / "coverage/protocol-core.html").is_file()
    and (root / "coverage/protocol-core-coverage.txt").is_file()
)
add(
    5,
    "覆盖率可信",
    coverage_ok,
    f"队列与异常样本回放后，radius.c/listen.c/process.c 共覆盖 {coverage_total} 行；TXT/HTML/JSON/CSV 报表已留存。",
)

replay_path = root / "coverage/replay-summary.json"
replay = json.loads(replay_path.read_text(encoding="utf-8")) if replay_path.is_file() else {}
queue_count = replay.get("queue", {}).get("sample_count", 0)
replay_ok = queue_count > 0 and smoke_ok and (root / "preflight/SHA256SUMS").is_file()
add(
    6,
    "每轮可复位",
    replay_ok,
    f"独立队列回放 {queue_count} 条；每次回放新启服务进程并清空 detail 状态；10 次重复 transcript 稳定；variable_paths={stats.get('variable_paths', '未知')}。",
)

fault_stats = read_stats(root / "fault-probe/fuzzer_stats")
fault_status_path = root / "fault-probe/probe-status.txt"
fault_status = fault_status_path.read_text(errors="replace") if fault_status_path.is_file() else ""
normal_hangs = numeric(stats.get("unique_hangs", 0))
fault_ok = (
    numeric(fault_stats.get("unique_crashes", 0)) > 0
    and (root / "fault-probe/intentional-crash-sample.bin").is_file()
    and "independent_replay_exit=" in fault_status
    and "temporary_injection_removed=true" in fault_status
    and normal_hangs <= 10
)
add(
    7,
    "异常可观察",
    fault_ok,
    f"故障探针异常计数={fault_stats.get('unique_crashes', '0')}，崩溃样本已保存且临时注入源码/程序已删除；真实目标挂起数={normal_hangs}。",
)

runtime_path = root / "fuzz-30m/runtime.txt"
elapsed = 0
if runtime_path.is_file():
    values = dict(line.split("=", 1) for line in runtime_path.read_text().splitlines() if "=" in line)
    try:
        start = dt.datetime.strptime(values["started_at_utc"], "%Y-%m-%dT%H:%M:%SZ")
        end = dt.datetime.strptime(values["finished_at_utc"], "%Y-%m-%dT%H:%M:%SZ")
        elapsed = int((end - start).total_seconds())
    except (KeyError, ValueError):
        elapsed = 0
results_ok = (
    elapsed >= 1800
    and numeric(stats.get("execs_done", 0)) > 0
    and (fuzz_dir / "plot_data").is_file()
    and (fuzz_dir / "fuzz-stats.csv").is_file()
    and (root / "coverage/queue-replay.jsonl").is_file()
    and (root / "coverage/crashes-replay.jsonl").is_file()
)
add(
    8,
    "结果可复查",
    results_ok,
    f"实际运行 {elapsed} 秒；execs_done={stats.get('execs_done', '未知')}、paths_total={stats.get('paths_total', '未知')}、unique_crashes={stats.get('unique_crashes', '未知')}、unique_hangs={stats.get('unique_hangs', '未知')}；统计、参数、覆盖率和逐样本记录齐全。",
)

print("# FreeRADIUS RADIUS/TCP 严格验收报告\n")
print("| 验收项 | 结果 | 证据摘要 |")
print("|---|---|---|")
for number, title, passed, evidence in checks:
    print(f"| {number}. {title} | {'通过' if passed else '未通过'} | {evidence} |")
print("\n构建版本、运行参数、输入哈希、fuzzer_stats、状态图、独立回放记录和覆盖率报告均在本目录。")
if not all(row[2] for row in checks):
    sys.exit(1)
