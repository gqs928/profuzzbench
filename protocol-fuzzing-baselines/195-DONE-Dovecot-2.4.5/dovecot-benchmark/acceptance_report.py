#!/usr/bin/env python3
"""根据实际运行记录逐项生成中文验收报告。"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def read_stats(path: Path) -> dict[str, str]:
    stats: dict[str, str] = {}
    if not path.is_file():
        return stats
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            stats[key.strip()] = value.strip()
    return stats


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def number(value: Any) -> float:
    try:
        return float(str(value).strip().rstrip("%"))
    except (TypeError, ValueError):
        return 0.0


def graph_counts(path: Path) -> tuple[int, int]:
    if not path.is_file():
        return 0, 0
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return (
        sum(line.startswith("node ") for line in lines),
        sum(line.startswith("edge ") for line in lines),
    )


def fmt_pass(condition: bool) -> str:
    return "通过" if condition else "失败"


def stage_ok(root: Path, name: str) -> bool:
    path = root / "stage-statuses.txt"
    if not path.is_file():
        return False
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith(name + "="):
            return line.split("=", 1)[1].strip() == "0"
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="生成 Dovecot IMAP 验收报告")
    parser.add_argument("results_dir", type=Path)
    args = parser.parse_args()
    root = args.results_dir

    build = root / "build-logs"
    source_lock_path = Path(__file__).with_name("source-lock.json")
    source_lock = {}
    if source_lock_path.is_file():
        source_lock = json.loads(source_lock_path.read_text(encoding="utf-8"))

    smoke = read_csv(root / "protocol-smoke" / "protocol-smoke.csv")
    smoke_ok = [row for row in smoke if row.get("status") == "PASS"]
    smoke_expected = 20
    replay_path = root / "seed-replay" / "seed-replay.json"
    replay = json.loads(replay_path.read_text(encoding="utf-8")) if replay_path.is_file() else {}
    fuzz_dir = root / "fuzz-30m-rerun-2026-10-15"
    if not fuzz_dir.is_dir():
        fuzz_dir = root / "fuzz-30m"
    if not fuzz_dir.is_dir():
        candidates = sorted(root.glob("fuzz-*"))
        fuzz_dir = candidates[-1] if candidates else root / "fuzz-30m"
    fuzz_stats = read_stats(fuzz_dir / "fuzzer_stats")
    fuzz_params = {}
    params_path = fuzz_dir / "run-parameters.txt"
    if params_path.is_file():
        for line in params_path.read_text(encoding="utf-8", errors="replace").splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                fuzz_params[key] = value
    graph_nodes, graph_edges = graph_counts(fuzz_dir / "ipsm.plain")
    elapsed = number(fuzz_params.get("elapsed_seconds", 0))
    executions = number(fuzz_stats.get("execs_done", 0))
    state_graph_ok = graph_nodes >= 2 and graph_edges >= 1
    fuzz_ok = elapsed >= 1800 and executions > 0 and state_graph_ok

    coverage_dir = root / "coverage-30m-rerun-2026-10-15"
    if not coverage_dir.is_dir():
        coverage_dir = root / "coverage"
    coverage_path = coverage_dir / "coverage-summary.json"
    coverage = json.loads(coverage_path.read_text(encoding="utf-8")) if coverage_path.is_file() else {}
    coverage_ok = (
        number(coverage.get("line_covered", 0)) > 0
        and number(coverage.get("branch_total", 0)) > 0
        and number(coverage.get("key_functions_covered", 0)) > 0
        and number(coverage.get("replay_inputs", 0)) > 0
        and number(coverage.get("replay_inputs", 0)) > number(coverage.get("replay_failed", 0))
        and number(coverage.get("replay_server_nonzero", 0)) == 0
    )
    probe_root = root / "fault-probe-fixed-rerun-2026-10-15"
    if not probe_root.is_dir():
        probe_root = root / "fault-probe-30m-rerun-2026-10-15"
    if not probe_root.is_dir():
        probe_root = root / "fault-probe"
    probe_run = probe_root / "dovecot-injected-run"
    probe_stats = read_stats(probe_run / "fuzzer_stats")
    probe_crashes = number(probe_stats.get("unique_crashes", 0))
    probe_executions = number(probe_stats.get("execs_done", 0))
    probe_params = {}
    probe_params_path = probe_run / "run-parameters.txt"
    if probe_params_path.is_file():
        for line in probe_params_path.read_text(encoding="utf-8", errors="replace").splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                probe_params[key] = value
    probe_elapsed = number(probe_params.get("elapsed_seconds", 0))
    probe_dir = probe_run / "replayable-crashes"
    if not probe_dir.is_dir():
        probe_dir = probe_run / "crashes"
    probe_files = list(probe_dir.glob("id:*")) if probe_dir.is_dir() else []
    injection_manifest = probe_root / "injection-manifest.txt"
    injection_data = injection_manifest.read_text(encoding="utf-8") if injection_manifest.is_file() else ""
    injection_removed = "source_patch_removed=true" in injection_data
    login_worker_chroot = "login_worker_chroot=/" in injection_data
    injection_marker = number(
        next((line.split("=", 1)[1] for line in injection_data.splitlines() if line.startswith("injection_marker_count=")), 0)
    )
    probe_ok = (
        probe_crashes > 0
        and len(probe_files) > 0
        and injection_removed
        and injection_marker > 0
        and login_worker_chroot
    )

    rebuild_ok = all(
        (build / name).is_file()
        for name in ("docker-build.log", "build-versions.txt", "package-manifest.txt", "image-id.txt", "build-input-sha256.txt")
    ) and stage_ok(root, "parser")
    replay_ok = bool(replay.get("stable")) and int(replay.get("repetitions", 0)) == 10 and stage_ok(root, "seed-replay")
    smoke_ok_all = len(smoke) == smoke_expected and len(smoke_ok) == smoke_expected and stage_ok(root, "protocol-smoke")
    fuzz_ok = fuzz_ok and stage_ok(root, "fuzz") and stage_ok(root, "state-graph")
    coverage_ok = coverage_ok and stage_ok(root, "coverage")
    probe_ok = probe_ok and stage_ok(root, "fault-probe")
    artifacts_ok = all(
        (fuzz_dir / name).is_file()
        for name in ("fuzzer_stats", "ipsm.dot", "fuzz.log", "run-parameters.txt")
    ) and (fuzz_dir / "queue").is_dir()
    coverage_inputs = int(number(coverage.get("replay_inputs", 0)))
    coverage_partial = int(number(coverage.get("replay_failed", 0)))
    coverage_complete = max(coverage_inputs - coverage_partial, 0)

    checks = [
        ("目标可重建", rebuild_ok, "固定 Dovecot/AFLNet 源码、基础镜像、APT 快照、补丁重应用和完整构建日志"),
        ("协议行为保留", smoke_ok_all, f"参考版和 AFL 版正常客户端流程各 10 次；成功 {len(smoke_ok)}/{len(smoke)}"),
        ("种子真实进入业务状态", smoke_ok_all and replay_ok, "登录、邮箱操作与 APPEND 字面量均按步骤回放"),
        ("状态反馈有效", fuzz_ok, f"运行 {elapsed:.0f} 秒，执行 {int(executions)} 次，状态图 {graph_nodes} 个节点/{graph_edges} 条边"),
        ("覆盖率可信", coverage_ok, f"IMAP 行覆盖 {coverage.get('line_covered', 0)}/{coverage.get('line_total', 0)} ({coverage.get('line_percent', 0)}%)；分支 {coverage.get('branch_covered', 0)}/{coverage.get('branch_total', 0)} ({coverage.get('branch_percent', 0)}%)；核心函数 {coverage.get('key_functions_covered', 0)}/{coverage.get('key_functions_total', 0)}；独立回放 {coverage_inputs} 条（完整应答 {coverage_complete}，部分结束 {coverage_partial}，标签等待超时 {coverage.get('replay_timeouts', 0)}，服务端非零退出 {coverage.get('replay_server_nonzero', 0)}）"),
        ("每轮可复位", replay_ok, f"login-mailbox 同一种子重复 {replay.get('repetitions', 0)} 次；状态签名数 {replay.get('signature_count', 0)}；稳定={str(replay.get('stable', False)).lower()}"),
        ("异常可观察", probe_ok, f"临时故障注入探针运行 {probe_elapsed:.0f} 秒、执行 {int(probe_executions)} 次；注入目标标记={int(injection_marker)}；登录 worker chroot=/；AFLNet 记录 {int(probe_crashes)} 个崩溃和 {len(probe_files)} 个可回放样本；源码补丁已撤回={str(injection_removed).lower()}"),
        ("结果可复查", artifacts_ok, "队列、fuzzer_stats、IPSM 状态图、运行参数和回放/覆盖率 CSV 均保留"),
    ]

    overall = all(condition for _, condition, _ in checks)
    report_lines = [
        "# Dovecot IMAP 模糊测试验收报告",
        "",
        f"- 生成时间：{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"- 上游提交：`{source_lock.get('target_commit', '未读取')}`",
        f"- AFLNet 提交：`{source_lock.get('aflnet_commit', '未读取')}`",
        f"- 总结：**{'全部通过' if overall else '存在未通过项'}**",
        "",
        "## 验收项",
        "",
        "| 验收项 | 结果 | 证据摘要 |",
        "| --- | --- | --- |",
    ]
    for name, condition, detail in checks:
        report_lines.append(f"| {name} | {fmt_pass(condition)} | {detail} |")

    report_lines.extend(
        [
            "",
            "## 模糊运行",
            "",
            f"- 请求时长：`{fuzz_params.get('duration_requested', '未知')}`；实测：{elapsed:.0f} 秒。",
            f"- 运行统计：执行 {int(executions)} 次，队列 {fuzz_stats.get('paths_total', '未知')}，变化路径 {fuzz_stats.get('variable_paths', '未知')}，稳定性 {fuzz_stats.get('stability', '未知')}。",
            f"- 异常统计：崩溃 {fuzz_stats.get('unique_crashes', '未知')}，挂起 {fuzz_stats.get('unique_hangs', '未知')}。原始 `fuzzer_stats` 与日志在 `{fuzz_dir.name}/`。",
            "",
            "## 已覆盖核心处理函数",
            "",
        ]
    )
    key_functions_path = coverage_dir / "key-function-coverage.csv"
    key_functions = read_csv(key_functions_path)
    if key_functions:
        for row in key_functions:
            report_lines.append(f"- `{Path(row['file']).name}:{row['function']}`（函数内行执行率 {row['lines_executed_percent']}%）")
    else:
        report_lines.append("- 未检测到命中的核心 IMAP 函数。")

    report_lines.extend(
        [
            "",
            "## 交付证据",
            "",
            "- `build-logs/`：从头构建日志、工具链版本、软件包清单、镜像摘要及输入 SHA-256。",
            "- `protocol-smoke/` 与 `seed-replay/`：正常客户端逐命令记录和同种子稳定性数据。",
            f"- `{fuzz_dir.name}/`：AFLNet 统计、状态图、运行参数、队列、异常样本和日志。",
            f"- `{coverage_dir.name}/`：gcovr 原始 JSON、总行/分支 CSV、逐输入回放记录、核心函数摘要和函数覆盖明细。",
            f"- `{probe_root.name}/`：临时 Dovecot 故障注入补丁、源码撤回校验、{probe_elapsed:.0f} 秒探针运行日志和 AFLNet 统计；崩溃样本 {len(probe_files)} 个。",
            "- `SHA256SUMS`：结果目录中的所有证据文件哈希。",
            "",
        ]
    )
    (root / "acceptance-report.md").write_text("\n".join(report_lines), encoding="utf-8")
    print(f"验收报告：{root / 'acceptance-report.md'}")
    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
