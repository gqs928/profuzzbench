#!/usr/bin/env python3
"""用二进制 Kafka 客户端请求验证固定 Broker 会话和十轮可复位性。"""

from __future__ import annotations

import hashlib
import json
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

from prepare_seeds import api_versions, fetch, metadata, produce


HOST = "127.0.0.1"
PORT = 9092


def read_exact(sock: socket.socket, size: int) -> bytes:
    parts = bytearray()
    while len(parts) < size:
        chunk = sock.recv(size - len(parts))
        if not chunk:
            raise ConnectionError(f"响应在读取 {size} 字节时提前关闭")
        parts.extend(chunk)
    return bytes(parts)


def response(sock: socket.socket) -> bytes:
    prefix = read_exact(sock, 4)
    length = int.from_bytes(prefix, "big")
    if length < 4 or length > 16 * 1024 * 1024:
        raise ValueError(f"Kafka 响应长度异常：{length}")
    return prefix + read_exact(sock, length)


def error_code(api_key: int, payload: bytes) -> int | None:
    if api_key == 18 and len(payload) >= 10:
        return int.from_bytes(payload[8:10], "big", signed=True)
    if api_key == 0 and len(payload) >= 4 + 4 + 4 + 2 + len("fuzz-topic") + 4 + 4 + 2:
        cursor = 8
        topics = int.from_bytes(payload[cursor:cursor + 4], "big", signed=True)
        cursor += 4
        if topics < 1:
            return None
        topic_len = int.from_bytes(payload[cursor:cursor + 2], "big", signed=True)
        cursor += 2 + topic_len
        partitions = int.from_bytes(payload[cursor:cursor + 4], "big", signed=True)
        cursor += 4
        if partitions < 1 or cursor + 6 > len(payload):
            return None
        cursor += 4
        return int.from_bytes(payload[cursor:cursor + 2], "big", signed=True)
    return None


def wait_ready(process: subprocess.Popen[bytes], log_file: Path) -> None:
    deadline = time.monotonic() + 100
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"Kafka 启动进程已退出，状态={process.returncode}，日志={log_file}")
        try:
            with socket.create_connection((HOST, PORT), timeout=0.2):
                return
        except OSError:
            time.sleep(0.05)
    raise RuntimeError(f"Kafka 未在 100 秒内就绪，日志={log_file}")


def stop(process: subprocess.Popen[bytes]) -> int:
    if process.poll() is None:
        process.send_signal(signal.SIGTERM)
        try:
            return process.wait(timeout=20)
        except subprocess.TimeoutExpired:
            process.kill()
    return process.wait(timeout=5)


def one_round(index: int, variant: str, outdir: Path) -> tuple[list[dict[str, object]], dict[str, object], Path]:
    log_path = outdir / f"{variant}-broker-{index:02d}.log"
    env = os.environ.copy()
    env["ENABLE_AFL_AGENT"] = "1" if variant == "instrumented" else "0"
    env["ENABLE_JACOCO"] = "1" if variant == "instrumented" else "0"
    env["JACOCO_DESTFILE"] = str(outdir / f"{variant}.exec")
    with log_path.open("wb") as log:
        proc = subprocess.Popen(
            ["bash", "/home/ubuntu/experiments/start-kafka.sh"],
            stdout=log,
            stderr=subprocess.STDOUT,
            env=env,
            start_new_session=True,
        )
        session: list[dict[str, object]] = []
        try:
            wait_ready(proc, log_path)
            with socket.create_connection((HOST, PORT), timeout=5) as sock:
                sock.settimeout(20)
                requests = [
                    (18, api_versions(1)),
                    (3, metadata(2)),
                    (0, produce(3)),
                    (1, fetch(4)),
                ]
                for api_key, request_data in requests:
                    sock.sendall(request_data)
                    reply = response(sock)
                    correlation_id = int.from_bytes(reply[4:8], "big")
                    if correlation_id not in (1, 2, 3, 4):
                        raise AssertionError(f"API {api_key} 响应 correlation id 错误：{correlation_id}")
                    result = {
                        "api_key": api_key,
                        "correlation_id": correlation_id,
                        "response_bytes": len(reply),
                        "response_sha256": hashlib.sha256(reply).hexdigest(),
                        "api_error_code": error_code(api_key, reply),
                    }
                    if len(reply) <= 8:
                        raise AssertionError(f"API {api_key} 响应体为空")
                    if api_key in (18, 0) and result["api_error_code"] not in (None, 0):
                        raise AssertionError(f"API {api_key} 返回协议错误：{result['api_error_code']}")
                    session.append(result)
            kafka_home = Path(os.environ.get("KAFKA_HOME", "/home/ubuntu/experiments/kafka"))
            producer = subprocess.run(
                [str(kafka_home / "bin/kafka-console-producer.sh"),
                 "--bootstrap-server", f"{HOST}:{PORT}", "--topic", "fuzz-topic"],
                input=b"client-event\n", stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, timeout=30)
            if producer.returncode != 0:
                raise RuntimeError("官方 Kafka console producer 执行失败：" +
                                   producer.stderr.decode("utf-8", errors="replace")[-1000:])
            consumer = subprocess.run(
                [str(kafka_home / "bin/kafka-console-consumer.sh"),
                 "--bootstrap-server", f"{HOST}:{PORT}", "--topic", "fuzz-topic",
                 "--from-beginning", "--max-messages", "2"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
            consumer_output = consumer.stdout.decode("utf-8", errors="replace")
            if consumer.returncode != 0 or "client-event" not in consumer_output:
                raise RuntimeError("官方 Kafka console consumer 未读到写入记录：" +
                                   consumer.stderr.decode("utf-8", errors="replace")[-1000:])
            client_result = {
                "producer_exit_code": producer.returncode,
                "consumer_exit_code": consumer.returncode,
                "consumer_observed_raw_protocol_record": "benchmark-record" in consumer_output,
                "consumer_observed_cli_record": "client-event" in consumer_output,
                "consumer_output": consumer_output.splitlines(),
            }
        finally:
            returncode = stop(proc)
        if returncode not in (0, 143, -signal.SIGTERM):
            raise RuntimeError(f"Kafka 非正常停止，状态={returncode}，日志={log_path}")
    return session, client_result, log_path


def main() -> int:
    if len(sys.argv) not in (2, 3):
        print("用法：protocol_smoke.py 输出目录 [重复次数]", file=sys.stderr)
        return 2
    outdir = Path(sys.argv[1])
    repetitions = int(sys.argv[2]) if len(sys.argv) == 3 else int(
        os.environ.get("KAFKA_SMOKE_REPETITIONS", "10"))
    if repetitions < 1 or repetitions > 100:
        raise ValueError("重复次数必须在 1 到 100 之间")
    outdir.mkdir(parents=True, exist_ok=True)
    if any(outdir.iterdir()):
        raise RuntimeError(f"协议回放目录必须为空：{outdir}")

    sessions = []
    for variant in ("reference", "instrumented"):
        for index in range(1, repetitions + 1):
            transcript, client_result, _ = one_round(index, variant, outdir)
            sessions.append({"variant": variant, "transcript": transcript,
                             "official_client": client_result})
    normalized = [
        (row["variant"], [(item["api_key"], item["correlation_id"],
                           item["api_error_code"])
                          for item in row["transcript"]])
        for row in sessions
    ]
    by_variant = {
        variant: [item[1] for item in normalized if item[0] == variant]
        for variant in ("reference", "instrumented")
    }
    stable = (
        all(item == by_variant["reference"][0] for item in by_variant["reference"]) and
        all(item == by_variant["instrumented"][0] for item in by_variant["instrumented"]) and
        by_variant["reference"][0] == by_variant["instrumented"][0]
    )
    report = {
        "target": "Apache Kafka 4.4.0 single-node KRaft broker",
        "endpoint": f"tcp://{HOST}:{PORT}",
        "protocol_session": ["ApiVersions", "Metadata", "Produce", "Fetch"],
        "normal_client_flow": ["kafka-console-producer", "kafka-console-consumer"],
        "repetitions": repetitions,
        "stable_normalized_transcript": stable,
        "rounds": sessions,
    }
    (outdir / "protocol-smoke.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (outdir / "protocol-smoke.txt").write_text(
        f"重复次数：{repetitions}\n同一输入业务响应稳定：{'是' if stable else '否'}\n"
        f"参考版/插桩代理版各重复 {repetitions} 次\n"
        f"每轮请求：ApiVersions → Metadata → Produce → Fetch\n",
        encoding="utf-8")
    if not stable:
        raise AssertionError("重复回放的协议状态不一致")
    print(f"PASS：{repetitions} 轮真实 Kafka 客户端会话状态一致；证据：{outdir}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, AssertionError, ConnectionError) as exc:
        print(f"FAIL：{exc}", file=sys.stderr)
        raise SystemExit(1)
