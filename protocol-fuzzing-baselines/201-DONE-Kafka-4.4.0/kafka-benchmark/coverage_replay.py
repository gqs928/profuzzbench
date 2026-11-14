#!/usr/bin/env python3
"""在复位后的真实 Kafka Broker 上逐条回放 AFLNet 队列并收集 JaCoCo 数据。"""

from __future__ import annotations

import json
import os
import signal
import socket
import subprocess
import sys
import time
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path


HOST = "127.0.0.1"
PORT = 9092
MAX_INPUT_BYTES = 1_048_576
CORE_HANDLER_METHODS = (
    "handle", "handleApiVersionsRequest", "handleTopicMetadataRequest",
    "handleProduceRequest", "handleFetchRequest", "handleListOffsetRequest",
    "handleFindCoordinatorRequest", "handleFindCoordinatorRequestLessThanV4",
)


def queue_files(root: Path) -> list[Path]:
    return sorted((item for item in root.iterdir()
                   if item.is_file() and item.name.startswith("id:")),
                  key=lambda item: item.name)


def stop_broker(process: subprocess.Popen[bytes]) -> int:
    if process.poll() is None:
        process.send_signal(signal.SIGTERM)
        try:
            return process.wait(timeout=25)
        except subprocess.TimeoutExpired:
            process.kill()
    return process.wait(timeout=5)


def wait_ready(process: subprocess.Popen[bytes], deadline_seconds: int = 100) -> None:
    deadline = time.monotonic() + deadline_seconds
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"Kafka 启动失败，状态={process.returncode}")
        try:
            with socket.create_connection((HOST, PORT), timeout=0.2):
                return
        except OSError:
            time.sleep(0.05)
    raise RuntimeError("Kafka Broker 启动超时")


def send_frames(sock: socket.socket, data: bytes) -> int:
    cursor = 0
    responses = 0
    while cursor < len(data):
        remaining = len(data) - cursor
        if remaining < 4:
            sock.sendall(data[cursor:])
            break
        declared = int.from_bytes(data[cursor:cursor + 4], "big")
        frame_size = declared + 4
        if declared < 8 or frame_size > remaining:
            sock.sendall(data[cursor:])
            break
        sock.sendall(data[cursor:cursor + frame_size])
        cursor += frame_size
        try:
            sock.settimeout(1.2)
            prefix = bytearray()
            while len(prefix) < 4:
                chunk = sock.recv(4 - len(prefix))
                if not chunk:
                    return responses
                prefix.extend(chunk)
            response_length = int.from_bytes(prefix, "big")
            if response_length < 4 or response_length > MAX_INPUT_BYTES:
                return responses
            left = response_length
            while left:
                chunk = sock.recv(min(left, 65536))
                if not chunk:
                    return responses
                left -= len(chunk)
            responses += 1
        except (OSError, TimeoutError):
            break
    return responses


def replay_one(path: Path, data: bytes, outdir: Path, index: int,
               jacoco_file: Path) -> dict[str, object]:
    log_path = outdir / f"{index:06d}-{path.name.replace(':', '_')}.log"
    env = os.environ.copy()
    env["ENABLE_AFL_AGENT"] = "0"
    env["ENABLE_JACOCO"] = "1"
    env["JACOCO_DESTFILE"] = str(jacoco_file)
    with log_path.open("wb") as log:
        process = subprocess.Popen(
            ["bash", "/home/ubuntu/experiments/start-kafka.sh"],
            stdout=log,
            stderr=subprocess.STDOUT,
            env=env,
            start_new_session=True,
        )
        status = "replayed"
        error = ""
        response_count = 0
        sock: socket.socket | None = None
        try:
            wait_ready(process)
            sock = socket.create_connection((HOST, PORT), timeout=5)
            response_count = send_frames(sock, data)
            if process.poll() is not None and process.returncode not in (0,):
                status = "broker_exited"
                error = f"Broker 在样本处理后退出，状态={process.returncode}"
        except (OSError, RuntimeError, TimeoutError) as exc:
            status = "replay_error"
            error = str(exc)
        finally:
            if sock is not None:
                sock.close()
            returncode = stop_broker(process)
    if status == "replayed" and returncode not in (0, 143, -signal.SIGTERM):
        status = "broker_exited"
        error = f"Broker 在独立回放期间异常退出，状态={returncode}"
    return {
        "input": path.name,
        "status": status,
        "input_bytes": len(data),
        "responses": response_count,
        "broker_returncode_after_shutdown": returncode,
        "error": error,
        "log": str(log_path),
    }


def class_and_source_args(source: Path) -> tuple[list[str], list[str]]:
    # 源码构建时从 Gradle classes 目录取字节码；官方发行版模式直接分析同版本 runtime JAR。
    classes = sorted(path for path in source.rglob("classes")
                     if path.is_dir() and path.parent.name == "build")
    sources = sorted(path for path in source.rglob("java")
                     if path.is_dir() and path.parent.name == "main"
                     and path.parent.parent.name == "src")
    sources.extend(sorted(path for path in source.rglob("scala")
                          if path.is_dir() and path.parent.name == "main"
                          and path.parent.parent.name == "src"))
    class_args: list[str] = []
    source_args: list[str] = []
    for path in classes:
        class_args.extend(["--classfiles", str(path)])
    if not class_args:
        kafka_home = Path(os.environ.get("KAFKA_HOME", "/home/ubuntu/experiments/kafka"))
        libraries = sorted((kafka_home / "libs").glob("kafka*.jar"))
        target_class = "kafka/server/KafkaApis.class"
        matching = []
        for jar_path in libraries:
            try:
                with zipfile.ZipFile(jar_path) as jar:
                    if target_class in jar.namelist():
                        matching.append(jar_path)
            except zipfile.BadZipFile:
                continue
        if not matching:
            raise RuntimeError(
                f"Kafka 编译类目录不存在，且官方发行包中找不到 {target_class}：{kafka_home / 'libs'}")
        # 交给 JaCoCo 全部 Kafka runtime 模块，确保执行数据里的 Kafka 类都能解析。
        for path in libraries:
            class_args.extend(["--classfiles", str(path)])
    for path in sources:
        source_args.extend(["--sourcefiles", str(path)])
    if not class_args:
        raise RuntimeError(f"Kafka 编译类目录或发行包 Jar 不存在：{source}")
    return class_args, source_args


def summarize_csv(csv_path: Path, output_csv: Path, summary_path: Path) -> dict[str, int]:
    import csv

    rows = []
    totals = {"lines_covered": 0, "lines_missed": 0,
              "branches_covered": 0, "branches_missed": 0}
    with csv_path.open(encoding="utf-8", newline="") as source:
        reader = csv.DictReader(source)
        for row in reader:
            package = row.get("PACKAGE", "")
            class_name = row.get("CLASS", "")
            # Kafka 4.x 的请求分派实现在 kafka.server.KafkaApis；排除测试类，只汇总该处理类及内部类。
            is_kafka_apis = package == "kafka.server" and class_name.startswith("KafkaApis") \
                and not class_name.startswith("KafkaApisTest")
            if not is_kafka_apis:
                continue
            rows.append(row)
            totals["lines_covered"] += int(row.get("LINE_COVERED", "0"))
            totals["lines_missed"] += int(row.get("LINE_MISSED", "0"))
            totals["branches_covered"] += int(row.get("BRANCH_COVERED", "0"))
            totals["branches_missed"] += int(row.get("BRANCH_MISSED", "0"))
    if not rows:
        raise RuntimeError("JaCoCo CSV 中没有 Kafka 请求解析或网络服务端核心类")
    with output_csv.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    lines_total = totals["lines_covered"] + totals["lines_missed"]
    branches_total = totals["branches_covered"] + totals["branches_missed"]
    summary = {
        **totals,
        "line_coverage_percent": round(100 * totals["lines_covered"] / lines_total, 2)
        if lines_total else 0,
        "branch_coverage_percent": round(100 * totals["branches_covered"] / branches_total, 2)
        if branches_total else 0,
        "included_classes": len(rows),
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8")
    return summary


def summarize_covered_methods(xml_path: Path, output_path: Path) -> list[str]:
    """列出真实队列回放命中的 KafkaApis 协议处理函数及其行覆盖。"""
    root = ET.parse(xml_path).getroot()
    covered: list[str] = []
    for package in root.findall("package"):
        if package.get("name") != "kafka/server":
            continue
        for class_node in package.findall("class"):
            if class_node.get("name") != "kafka/server/KafkaApis":
                continue
            for method in class_node.findall("method"):
                name = method.get("name", "")
                if name not in CORE_HANDLER_METHODS:
                    continue
                line_counter = next((counter for counter in method.findall("counter")
                                     if counter.get("type") == "LINE"), None)
                if line_counter is None:
                    continue
                covered_lines = int(line_counter.get("covered", "0"))
                missed_lines = int(line_counter.get("missed", "0"))
                if covered_lines:
                    covered.append(
                        f"kafka.server.KafkaApis#{name}：{covered_lines}/"
                        f"{covered_lines + missed_lines} 行"
                    )
    output_path.write_text("\n".join(covered) + "\n", encoding="utf-8")
    return covered


def main() -> int:
    if len(sys.argv) != 4:
        print("用法：coverage_replay.py AFL队列 异常队列 输出目录", file=sys.stderr)
        return 2
    queue_dir, crash_dir, outdir = map(Path, sys.argv[1:])
    if not queue_dir.is_dir():
        raise RuntimeError(f"AFLNet 队列不存在：{queue_dir}")
    outdir.mkdir(parents=True, exist_ok=True)
    if any(outdir.iterdir()):
        raise RuntimeError(f"覆盖率输出目录必须为空：{outdir}")
    queue = queue_files(queue_dir)
    crashes = queue_files(crash_dir) if crash_dir.is_dir() else []
    if not queue:
        raise RuntimeError("AFLNet 队列没有 id: 样本")
    jacoco_file = outdir / "kafka-queue.exec"
    outcomes = []
    for index, path in enumerate(queue + crashes):
        data = path.read_bytes()
        if len(data) > MAX_INPUT_BYTES:
            outcomes.append({"input": path.name, "status": "skipped_oversize",
                             "input_bytes": len(data), "responses": 0})
            continue
        result = replay_one(path, data, outdir, index, jacoco_file)
        result["corpus"] = "crash" if path in crashes else "queue"
        outcomes.append(result)
        journal_name = "crashes-replay.jsonl" if path in crashes else "queue-replay.jsonl"
        with (outdir / journal_name).open("a", encoding="utf-8") as journal:
            journal.write(json.dumps(result, ensure_ascii=False) + "\n")

    for journal_name in ("queue-replay.jsonl", "crashes-replay.jsonl"):
        (outdir / journal_name).touch(exist_ok=True)

    if not jacoco_file.is_file() or jacoco_file.stat().st_size == 0:
        raise RuntimeError("真实 Broker 回放没有生成 JaCoCo 执行数据")
    cli = os.environ.get("JACOCO_CLI", "/home/ubuntu/agents/jacococli.jar")
    source = Path(os.environ.get("KAFKA_SOURCE", "/home/ubuntu/experiments/kafka-source"))
    class_args, source_args = class_and_source_args(source)
    html_dir = outdir / "jacoco-html"
    csv_path = outdir / "jacoco-all.csv"
    xml_path = outdir / "jacoco-all.xml"
    subprocess.run(["java", "-jar", cli, "report", str(jacoco_file),
                    *class_args, *source_args,
                    "--html", str(html_dir), "--csv", str(csv_path),
                    "--xml", str(xml_path)], check=True)
    summary = summarize_csv(csv_path, outdir / "protocol-core-coverage.csv",
                            outdir / "protocol-core-coverage.json")
    covered_methods = summarize_covered_methods(xml_path, outdir / "covered-functions.txt")
    if not covered_methods:
        raise RuntimeError("JaCoCo XML 中没有 KafkaApis 核心处理函数的已覆盖行")
    report = {
        "queue_inputs": len(queue),
        "crash_inputs": len(crashes),
        "replayed": sum(row["status"] == "replayed" for row in outcomes),
        "broker_exits": sum(row["status"] == "broker_exited" for row in outcomes),
        "replay_errors": sum(row["status"] == "replay_error" for row in outcomes),
        "oversize_skipped": sum(row["status"] == "skipped_oversize" for row in outcomes),
        "coverage": summary,
        "covered_core_methods": covered_methods,
        "results": outcomes,
    }
    (outdir / "coverage-replay.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (outdir / "protocol-core-coverage.txt").write_text(
        "Kafka 请求处理类 kafka.server.KafkaApis 覆盖率（JaCoCo）\n"
        f"逐样本回放：{report['replayed']}\n"
        f"Broker 异常退出：{report['broker_exits']}\n"
        f"行覆盖：{summary['lines_covered']}/{summary['lines_covered'] + summary['lines_missed']} "
        f"({summary['line_coverage_percent']}%)\n"
        f"分支覆盖：{summary['branches_covered']}/{summary['branches_covered'] + summary['branches_missed']} "
        f"({summary['branch_coverage_percent']}%)\n",
        encoding="utf-8")
    with (outdir / "protocol-core-coverage.txt").open("a", encoding="utf-8") as output:
        output.write("已覆盖核心处理函数：\n")
        output.writelines(f"- {method}\n" for method in covered_methods)
    print(f"PASS：独立回放 {report['replayed']} 个输入；Kafka 核心行覆盖率 "
          f"{summary['line_coverage_percent']}%，分支覆盖率 {summary['branch_coverage_percent']}%")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"FAIL：{exc}", file=sys.stderr)
        raise SystemExit(1)
