#!/usr/bin/env python3
"""按用户给定的 8 项验收表核对证据并输出中文结果。"""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


def parse_stats(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for line in path.read_text(errors="replace").splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            values[key.strip()] = value.strip()
    return values


def main() -> int:
    if len(sys.argv) != 2:
        print("用法：acceptance_report.py 结果目录", file=sys.stderr)
        return 2
    root = Path(sys.argv[1])
    build_text = (root / "build-versions.txt").read_text(errors="replace") \
        if (root / "build-versions.txt").is_file() else ""
    smoke = load_json(root / "protocol-smoke/protocol-smoke.json")
    seeds = load_json(root / "seed-replay/seed-replay.json")
    fuzz = root / "fuzz-run-02"
    if not (fuzz / "fuzzer_stats").is_file():
        fuzz = root / "fuzz-run-01"
    fuzz_stats = parse_stats(fuzz / "fuzzer_stats")
    probe_stats = parse_stats(root / "fault-probe/aflnet/fuzzer_stats")
    coverage_summary_path = root / "coverage/coverage-core-summary.json"
    if not coverage_summary_path.is_file():
        coverage_summary_path = root / "coverage/coverage/coverage-core-summary.json"
    coverage_dir = coverage_summary_path.parent
    coverage = load_json(coverage_summary_path)
    replay = load_json(root / "coverage/replay/replay-summary.json")
    probe = load_json(root / "fault-probe/independent-replay/replay.json")
    graph_path = fuzz / "ipsm.dot"
    graph = graph_path.read_text(errors="replace") if graph_path.is_file() else ""
    graph_nodes = {int(value) for value in re.findall(
        r"^\s*(\d+)\s+\[color=", graph, re.M)}
    graph_edges = len(re.findall(r"^\s*\d+\s*->\s*\d+\s+\[key=", graph, re.M))
    core_files = coverage.get("files", [])
    core_functions = coverage.get("functions", [])
    covered_core_lines = sum(int(item.get("covered_lines", 0)) for item in core_files)
    core_branches = sum(int(item.get("branches", 0)) for item in core_files)
    covered_functions = {str(item.get("function")) for item in core_functions
                         if item.get("covered")}
    business = seeds.get("business_flows", {})
    exec_value = fuzz_stats.get("execs_done", "0").split()
    crash_value = fuzz_stats.get("unique_crashes", "0").split()
    hang_value = fuzz_stats.get("unique_hangs", "0").split()
    probe_crash_value = probe_stats.get("unique_crashes", "0").split()
    stats_execs = int(exec_value[0]) if exec_value else 0
    stats_crashes = int(crash_value[0]) if crash_value else 0
    stats_hangs = int(hang_value[0]) if hang_value else 0
    probe_crashes = int(probe_crash_value[0]) if probe_crash_value else 0
    source_checks = root / "source-checksums.log"
    evidence_hashes = root / "SHA256SUMS"
    stable = seeds.get("stable_transcripts_match") is True \
        and seeds.get("stable_repetitions") == 10
    checks = [
        (
            "1. 目标可重建",
            "Dockerfile、固定源码/依赖版本、源码 SHA-256、镜像 ID 与构建日志",
            "18.6" in build_text and "aflnet_commit=" in build_text
            and source_checks.is_file() and evidence_hashes.is_file()
            and (root / "build/image-id.txt").is_file()
            and (root / "build/docker-build.log").is_file(),
        ),
        (
            "2. 协议行为保留",
            "原版与 AFL 插桩版正常客户端 10 轮 transcript 对照",
            smoke.get("all_transcripts_match") is True
            and smoke.get("repetitions_per_build", 0) >= 10
            and len(smoke.get("comparisons", [])) >= 10,
        ),
        (
            "3. 种子进入业务状态",
            "逐种子响应记录；查询、事务恢复、扩展查询、COPY、登录结果状态",
            bool(business) and all(item.get("passed") for item in business.values())
            and seeds.get("seed_replays_succeeded") == seeds.get("seed_count"),
        ),
        (
            "4. 状态反馈有效",
            "AFLNet fuzzer_stats、ipsm.dot/CSV 与 PostgreSQL 响应状态映射",
            stats_execs > 0 and graph_edges > 0
            and {10, 20, 21, 22}.issubset(graph_nodes),
        ),
        (
            "5. 覆盖率可信",
            "独立 gcov 构建回放、协议核心行/分支 CSV、关键函数覆盖情况",
            len(core_files) >= 4 and covered_core_lines > 0 and core_branches > 0
            and bool(covered_functions)
            and (coverage_dir / "protocol-core-coverage.csv").is_file()
            and {"PostgresMain", "exec_simple_query", "exec_parse_message",
                 "exec_bind_message", "exec_execute_message"}.issubset(covered_functions)
            and replay.get("samples_replayed", 0) > 0,
        ),
        (
            "6. 每轮可复位",
            "每个样本新建临时 PGDATA；固定种子重放 10 次 transcript 一致",
            stable and "新临时目录" in str(seeds.get("reset_policy", "")),
        ),
        (
            "7. 异常可观察",
            "AFLNet 故障探针崩溃样本、独立 SIGABRT 重放及服务日志",
            probe.get("connected_and_replayed") is True
            and probe.get("expected_sigabrt") is True
            and probe_crashes > 0
            and (root / "fault-probe/independent-replay/server.log").is_file(),
        ),
        (
            "8. 结果可复查",
            "运行参数、fuzzer_stats、plot_data/CSV、逐样本日志及证据 SHA-256",
            (fuzz / "run-parameters.txt").is_file()
            and (fuzz / "fuzzer_stats").is_file()
            and (fuzz / "plot_data").is_file()
            and (fuzz / "fuzz-stats.csv").is_file()
            and (root / "coverage/replay/queue-replay.jsonl").is_file()
            and evidence_hashes.is_file(),
        ),
    ]
    rows = [{
        "验收项": title,
        "结果": "通过" if passed else "未通过",
        "应提交证据": evidence,
    } for title, evidence, passed in checks]
    with (root / "acceptance-report.csv").open(
            "w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=["验收项", "结果", "应提交证据"])
        writer.writeheader()
        writer.writerows(rows)
    markdown = [
        "# PostgreSQL 协议模糊测试基准验收报告", "",
        f"- 构建目标：PostgreSQL 18.6；AFLNet 执行次数：{stats_execs}",
        f"- 可回放崩溃 / 挂起：{stats_crashes} / {stats_hangs}",
        f"- 核心覆盖文件：{len(core_files)}；已覆盖关键函数：{len(covered_functions)}",
        f"- 队列/异常样本独立回放：{replay.get('samples_replayed', 0)}/"
        f"{replay.get('samples_total', 0)}", "",
        "| 验收项 | 结果 | 应提交证据 |", "|---|---|---|",
    ]
    markdown.extend(f"| {title} | {'通过' if passed else '未通过'} | {evidence} |"
                    for title, evidence, passed in checks)
    markdown.extend(["", "故障探针是专门验证 AFLNet 崩溃记录/独立回放链路的测试程序；"
                     "其 SIGABRT 不表示 PostgreSQL 本身存在已知崩溃。", ""])
    (root / "acceptance-report.md").write_text("\n".join(markdown), encoding="utf-8")
    (root / "acceptance-report.json").write_text(json.dumps({
        "checks": [{"item": title, "evidence": evidence, "passed": passed}
                   for title, evidence, passed in checks],
        "all_passed": all(passed for _, _, passed in checks),
        "fuzzer_execs": stats_execs,
        "fuzzer_crashes": stats_crashes,
        "fuzzer_hangs": stats_hangs,
        "fault_probe_crashes": probe_crashes,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print((root / "acceptance-report.md").read_text(encoding="utf-8"))
    return 0 if all(passed for _, _, passed in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
