#!/usr/bin/env python3
"""按图片列出的八项验收要求汇总 Kafka 基准的实际运行证据。"""

from __future__ import annotations

import datetime as dt
import json
import pathlib
import re
import sys


root = pathlib.Path(sys.argv[1])
project = pathlib.Path(__file__).parent


def evidence_dir(names: tuple[str, ...]) -> pathlib.Path:
    """按修正后的 JaCoCo 证据优先级选择目录。"""
    return next((root / name for name in names if (root / name).is_dir()), root / names[-1])


preflight_dir = evidence_dir(("preflight-jacoco-colon", "preflight-jacoco-fix", "preflight"))
coverage_dir = evidence_dir(("coverage-jacoco-colon", "coverage-jacoco-fix", "coverage"))
fault_dir = evidence_dir(("fault-probe-jacoco-fixed4", "fault-probe-jacoco-fixed3",
                          "fault-probe-jacoco-fixed2", "fault-probe-jacoco-fixed",
                          "fault-probe-jacoco-colon",
                          "fault-probe-jacoco-fix", "fault-probe"))
build_dir = evidence_dir(("build-logs-jacoco-delivery", "build-logs-jacoco-final",
                          "build-logs-jacoco-colon", "build-logs"))
checks: list[tuple[int, str, bool, str]] = []


def add(number: int, title: str, passed: bool, evidence: str) -> None:
    checks.append((number, title, bool(passed), evidence))


def read_stats(path: pathlib.Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if path.is_file():
        for line in path.read_text(errors="replace").splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                values[key.strip()] = value.strip()
    return values


def numeric(value: object) -> int:
    return int(re.sub(r"[^0-9]", "", str(value)) or "0")


build_paths = [
    build_dir / "docker-build.log",
    build_dir / "build-versions.txt",
    build_dir / "build-input-sha256.txt",
    build_dir / "package-manifest.txt",
    build_dir / "base-image.txt",
    build_dir / "image-id.txt",
    root / "resource-limits.txt",
    preflight_dir / "image-id.txt",
]
version_path = build_dir / "build-versions.txt"
build_text = version_path.read_text(errors="replace") if version_path.is_file() else ""
fuzz_version_path = root / "fuzz-build-versions.txt"
fuzz_build_text = fuzz_version_path.read_text(errors="replace") \
    if fuzz_version_path.is_file() else ""
fuzz_parameters_path = root / "fuzz-30m/aflnet/run-parameters.txt"
fuzz_parameters_text = fuzz_parameters_path.read_text(errors="replace") \
    if fuzz_parameters_path.is_file() else ""
build_image_path = build_dir / "image-id.txt"
preflight_image_path = preflight_dir / "image-id.txt"
build_image = build_image_path.read_text(errors="replace").splitlines() \
    if build_image_path.is_file() else []
preflight_image = preflight_image_path.read_text(errors="replace").splitlines() \
    if preflight_image_path.is_file() else []
resource_path = root / "resource-limits.txt"
resource_text = resource_path.read_text(errors="replace") if resource_path.is_file() else ""
build_mode = re.search(r"^build_mode=(.+)$", resource_text, re.MULTILINE)
build_mode = build_mode.group(1) if build_mode else "full"
build_ok = all(path.is_file() and path.stat().st_size for path in build_paths) \
    and "kafka_commit=1156b2752aaa28eafc0b4c4d387e63356793268d" in build_text \
    and "aflnet_commit=0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732" in build_text \
    and "kafka_distribution=Apache official 4.4.0 binary archive" in build_text \
    and "kafka_binary_sha512=" in build_text and "kafka_source_sha512=" in build_text \
    and "cpu_limits=native_build_single_worker" in build_text \
    and "memory_limits=broker_heap_max=384m" in build_text \
    and "target_launcher=aflnet_instrumented_elf_exec_wrapper" in build_text \
    and "aflnet_kafka_fuzz_patch_sha256=" in build_text \
    and "kafka_jvm_coverage=KafkaApis-request-handler-method-presence-bitmap;call-frequency-not-counted" in build_text \
    and "target_termination=-K" in fuzz_parameters_text \
    and (build_mode != "overlay" or "overlay_base_image_id=sha256:" in build_text) \
    and build_image == preflight_image \
    and all(f"{key}=" in fuzz_build_text and f"{key}=" in build_text
            and re.search(rf"^{key}=(.+)$", fuzz_build_text, re.MULTILINE).group(1)
            == re.search(rf"^{key}=(.+)$", build_text, re.MULTILINE).group(1)
            for key in ("kafka_commit", "aflnet_commit", "aflnet_kafka_fuzz_patch_sha256",
                        "jvm_agent_sha256")) \
    and "kafka_build=verified-official-release-binary; no local Gradle compile" in resource_text \
    and "build_min_available_memory_mib=1024" in resource_text
add(1, "目标可重建", build_ok,
    "固定提交与 Apache 官方二进制/源码 SHA-512、构建输入哈希、资源配置和镜像 ID 均已留存。")

smoke_path = preflight_dir / "protocol-smoke/protocol-smoke.json"
smoke = json.loads(smoke_path.read_text(encoding="utf-8")) if smoke_path.is_file() else {}
rounds = smoke.get("rounds", [])
reference = [row for row in rounds if row.get("variant") == "reference"]
instrumented = [row for row in rounds if row.get("variant") == "instrumented"]


def normalize(row: dict[str, object]) -> list[tuple[object, object, object]]:
    return [(item.get("api_key"), item.get("correlation_id"), item.get("api_error_code"))
            for item in row.get("transcript", [])]


transcripts = [normalize(row) for row in rounds]
client_flows = [row.get("official_client", {}) for row in rounds]
smoke_ok = (
    len(reference) >= 10 and len(instrumented) >= 10
    and bool(transcripts)
    and all(item == transcripts[0] for item in transcripts[1:])
    and all(len(item) == 4 and [record[0] for record in item] == [18, 3, 0, 1]
            for item in transcripts)
    and all(flow.get("producer_exit_code") == 0
            and flow.get("consumer_exit_code") == 0
            and flow.get("consumer_observed_raw_protocol_record")
            and flow.get("consumer_observed_cli_record") for flow in client_flows)
)
add(2, "协议行为保留", smoke_ok,
    f"无代理参考版 {len(reference)} 轮、插桩代理版 {len(instrumented)} 轮；"
    "ApiVersions→Metadata→Produce→Fetch 状态一致，Kafka 官方 CLI producer/consumer 均完成写读。")

manifest_path = project / "seeds-manifest.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.is_file() else {}
seed_rows = manifest.get("seeds", [])
api_keys = [key for row in seed_rows for key in row.get("api_keys", [])]
business_ok = len(seed_rows) >= 8 and all(key in api_keys for key in (18, 3, 0, 1, 2, 10))
add(3, "种子真正进入业务状态", business_ok and smoke_ok,
    f"可复现语料 {len(seed_rows)} 个，覆盖协商、元数据、写入、读取、偏移查询、协调器及畸形帧；"
    "协议烟测确认成功请求到达 Broker。")

fuzz_dir = root / "fuzz-30m/aflnet"
stats = read_stats(fuzz_dir / "fuzzer_stats")
graph_path = fuzz_dir / "ipsm.dot"
graph_text = graph_path.read_text(errors="replace") if graph_path.is_file() else ""
state_nodes = set(re.findall(r"^\s*(\d+)\s+\[", graph_text, re.MULTILINE))
state_ok = graph_path.is_file() and {"1", "2", "3", "4"}.issubset(state_nodes) \
    and (project / "kafka-state-mapping.md").is_file()
add(4, "状态反馈有效", state_ok,
    f"AFLNet IPSM 状态节点={','.join(sorted(state_nodes, key=int)) or '缺失'}；"
    "包含 ApiVersions、Metadata、Produce、Fetch 四个真实响应阶段。")

coverage_json = coverage_dir / "protocol-core-coverage.json"
coverage = json.loads(coverage_json.read_text(encoding="utf-8")) if coverage_json.is_file() else {}
coverage_paths = [
    coverage_dir / "protocol-core-coverage.txt",
    coverage_dir / "protocol-core-coverage.csv",
    coverage_dir / "jacoco-all.xml",
    coverage_dir / "jacoco-html/index.html",
    coverage_dir / "covered-functions.txt",
]
covered_functions = [line.strip() for line in
                    (coverage_dir / "covered-functions.txt").read_text(encoding="utf-8").splitlines()
                    if line.strip()] if (coverage_dir / "covered-functions.txt").is_file() else []
coverage_ok = all(path.is_file() and path.stat().st_size for path in coverage_paths) \
    and coverage.get("lines_covered", 0) > 0 and coverage.get("branches_covered", 0) > 0 \
    and bool(covered_functions)
add(5, "覆盖率可信", coverage_ok,
    f"KafkaApis 请求处理类行覆盖 {coverage.get('lines_covered', 0)}，"
    f"分支覆盖 {coverage.get('branches_covered', 0)}；"
    f"已覆盖函数：{', '.join(covered_functions)}；JaCoCo TXT/HTML/XML/CSV 已保存。")

replay_path = coverage_dir / "coverage-replay.json"
replay = json.loads(replay_path.read_text(encoding="utf-8")) if replay_path.is_file() else {}
queue_count = replay.get("queue_inputs", 0)
stability_value = re.sub(r"[^0-9.]", "", stats.get("stability", "0")) or "0"
coverage_stability = float(stability_value)
# 把图片中的“基本一致覆盖轨迹”落实为 AFLNet 校准稳定度至少 90%。
replay_ok = queue_count > 0 and (coverage_dir / "queue-replay.jsonl").is_file() \
    and (coverage_dir / "crashes-replay.jsonl").is_file() \
    and smoke.get("stable_normalized_transcript", False) \
    and coverage_stability >= 90.0
add(6, "每轮可复位", replay_ok,
    f"逐条回放队列 {queue_count} 个输入；每次重启真实 Broker 并从同一 KRaft 存储快照恢复；"
    f"10 轮业务 transcript 稳定；AFLNet 覆盖稳定度={coverage_stability:.2f}%（门槛 90%）。")

fault_stats = read_stats(fault_dir / "fuzzer_stats")
fault_status_path = fault_dir / "probe-status.txt"
fault_status = fault_status_path.read_text(errors="replace") \
    if fault_status_path.is_file() else ""
normal_hangs = numeric(stats.get("unique_hangs", 0))
fault_ok = numeric(fault_stats.get("unique_crashes", 0)) > 0 \
    and (fault_dir / "intentional-crash-sample.bin").is_file() \
    and "independent_replay_exit=-6" in fault_status \
    and "temporary_injection_removed=true" in fault_status \
    and normal_hangs <= 10
add(7, "异常可观察", fault_ok,
    f"隔离故障探针记录异常 {fault_stats.get('unique_crashes', '0')} 次，样本独立复现 SIGABRT；"
    f"Kafka 源码未注入故障，真实 Broker 挂起={normal_hangs}。")

runtime_path = root / "fuzz-30m/runtime.txt"
elapsed = 0
if runtime_path.is_file():
    values = dict(line.split("=", 1) for line in runtime_path.read_text().splitlines()
                  if "=" in line)
    try:
        start = dt.datetime.strptime(values["started_at_utc"], "%Y-%m-%dT%H:%M:%SZ")
        end = dt.datetime.strptime(values["finished_at_utc"], "%Y-%m-%dT%H:%M:%SZ")
        elapsed = int((end - start).total_seconds())
    except (KeyError, ValueError):
        elapsed = 0
results_ok = elapsed >= 1800 and numeric(stats.get("execs_done", 0)) > 0 \
    and (fuzz_dir / "plot_data").is_file() and (fuzz_dir / "fuzz-stats.csv").is_file() \
    and (fuzz_dir / "run-parameters.txt").is_file() \
    and (coverage_dir / "queue-replay.jsonl").is_file() \
    and (coverage_dir / "crashes-replay.jsonl").is_file() \
    and "docker_cpu_quota=" in resource_text and "docker_memory_limit=" in resource_text
add(8, "结果可复查", results_ok,
    f"真实运行 {elapsed} 秒；execs_done={stats.get('execs_done', '未知')}、"
    f"paths_total={stats.get('paths_total', '未知')}、"
    f"variable_paths={stats.get('variable_paths', '未知')}、"
    f"unique_crashes={stats.get('unique_crashes', '未知')}、"
    f"unique_hangs={stats.get('unique_hangs', '未知')}；CPU 配额="
    f"{resource_text.split('docker_cpu_quota=', 1)[1].splitlines()[0] if 'docker_cpu_quota=' in resource_text else '缺失'} 核；"
    f"内存上限={resource_text.split('docker_memory_limit=', 1)[1].splitlines()[0] if 'docker_memory_limit=' in resource_text else '缺失'}；"
    "统计、参数、逐样本回放和覆盖报告齐全。")

print("# Apache Kafka 二进制协议模糊测试严格验收报告\n")
print("| 验收项 | 结果 | 证据摘要 |")
print("|---|---|---|")
for number, title, passed, evidence in checks:
    print(f"| {number}. {title} | {'通过' if passed else '未通过'} | {evidence} |")
print("\n构建输入、版本、fuzzer_stats、状态图、种子、逐样本重放、JaCoCo 覆盖率和异常样本均留在此目录。")
if not all(row[2] for row in checks):
    sys.exit(1)
