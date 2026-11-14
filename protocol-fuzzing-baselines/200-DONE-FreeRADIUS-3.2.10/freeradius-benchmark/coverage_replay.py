#!/usr/bin/env python3
"""在全新 FreeRADIUS 进程中逐条独立回放 AFLNet 队列和异常样本。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import signal
import socket
import subprocess
import sys
import time


def packet_codes(data: bytes) -> list[int]:
    result = []
    cursor = 0
    while cursor + 4 <= len(data):
        size = int.from_bytes(data[cursor + 2 : cursor + 4], "big")
        if size < 20 or cursor + size > len(data):
            break
        result.append(data[cursor])
        cursor += size
    return result


def decode_aflnet_messages(data: bytes) -> bytes:
    """还原 AFLNet 异常目录中以本机 32 位长度前缀保存的报文序列。"""
    messages = []
    cursor = 0
    while cursor < len(data):
        if cursor + 4 > len(data):
            raise ValueError("AFLNet 消息长度前缀不完整")
        size = int.from_bytes(data[cursor : cursor + 4], sys.byteorder)
        cursor += 4
        if size < 20 or cursor + size > len(data):
            raise ValueError(f"AFLNet 消息长度无效：{size}")
        messages.append(data[cursor : cursor + size])
        cursor += size
    if not messages:
        raise ValueError("AFLNet 异常样本不含 RADIUS 报文")
    return b"".join(messages)


def stop_process(process: subprocess.Popen) -> int | None:
    if process.poll() is None:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=4)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=4)
    return process.returncode


def replay(
    path: pathlib.Path, target: str, config: str, timeout: float, aflnet_framed: bool
) -> dict:
    stored_data = path.read_bytes()
    try:
        data = decode_aflnet_messages(stored_data) if aflnet_framed else stored_data
    except ValueError as error:
        return {
            "file": str(path),
            "sha256": hashlib.sha256(stored_data).hexdigest(),
            "bytes": len(stored_data),
            "input_format": "aflnet-length-prefixed" if aflnet_framed else "radius-stream",
            "requests": [],
            "responses": [],
            "server_exit_code": None,
            "connect_error": None,
            "exception": str(error),
        }
    result = {
        "file": str(path),
        "sha256": hashlib.sha256(stored_data).hexdigest(),
        "wire_sha256": hashlib.sha256(data).hexdigest(),
        "bytes": len(stored_data),
        "wire_bytes": len(data),
        "input_format": "aflnet-length-prefixed" if aflnet_framed else "radius-stream",
        "requests": packet_codes(data),
        "responses": [],
        "server_exit_code": None,
        "connect_error": None,
        "exception": None,
    }
    subprocess.run(["/workspace/clean.sh"], check=True)
    command = [target, "-f", "-l", "/dev/null", "-d", config]
    process = subprocess.Popen(
        command,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    deadline = time.monotonic() + 10
    sock = None
    while time.monotonic() < deadline:
        if process.poll() is not None:
            result["server_exit_code"] = process.returncode
            result["exception"] = "服务端在监听就绪前退出"
            return result
        try:
            sock = socket.create_connection(("127.0.0.1", 1812), timeout=0.2)
            break
        except OSError:
            time.sleep(0.05)
    if sock is None:
        result["connect_error"] = "TCP/1812 启动超时"
        result["server_exit_code"] = stop_process(process)
        return result

    try:
        sock.settimeout(timeout)
        sock.sendall(data)
        sock.shutdown(socket.SHUT_WR)
        response_data = bytearray()
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                part = sock.recv(65535)
            except socket.timeout:
                break
            if not part:
                break
            response_data.extend(part)
            if len(response_data) > 1_000_000:
                result["exception"] = "服务端响应超过回放上限"
                break
        result["responses"] = packet_codes(bytes(response_data))
    except (OSError, RuntimeError) as error:
        result["exception"] = f"{type(error).__name__}: {error}"
    finally:
        sock.close()
        result["server_exit_code"] = stop_process(process)
    return result


def sample_files(directory: pathlib.Path) -> list[pathlib.Path]:
    if not directory.is_dir():
        return []
    return sorted(path for path in directory.iterdir() if path.is_file() and path.name.startswith("id:"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--queue", required=True)
    parser.add_argument("--crashes", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--timeout", type=float, default=1.5)
    args = parser.parse_args()

    output = pathlib.Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    groups = {
        "queue": sample_files(pathlib.Path(args.queue)),
        "crashes": sample_files(pathlib.Path(args.crashes)),
    }
    summary = {}
    for name, files in groups.items():
        rows = []
        with (output / f"{name}-replay.jsonl").open("w", encoding="utf-8") as stream:
            for path in files:
                row = replay(
                    path,
                    args.target,
                    args.config,
                    args.timeout,
                    aflnet_framed=(name == "crashes"),
                )
                rows.append(row)
                stream.write(json.dumps(row, ensure_ascii=False) + "\n")
                stream.flush()
        summary[name] = {
            "sample_count": len(rows),
            "replayed_count": sum(
                row["connect_error"] is None and row["exception"] is None for row in rows
            ),
            "observed_abnormal_exits": sum(
                row["server_exit_code"] not in (None, 0, -signal.SIGTERM) for row in rows
            ),
            "response_packets": sum(len(row["responses"]) for row in rows),
            "exceptions": [row for row in rows if row["exception"] or row["connect_error"]],
        }
    (output / "replay-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["queue"]["sample_count"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
