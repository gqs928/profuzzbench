#!/usr/bin/env python3
"""在独立 gcov Asterisk 进程中逐条回放 AFLNet 队列及异常样本。"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import signal
import socket
import sys
import time

from sip_tools import (
    SIPReader,
    port_is_closed,
    response_code,
    start_server,
    stop_server,
    wait_listener,
)


def decode_aflnet_messages(data: bytes) -> list[bytes]:
    """还原 AFLNet 回放目录中的本机 32 位长度前缀消息序列。"""
    messages = []
    cursor = 0
    while cursor < len(data):
        if cursor + 4 > len(data):
            raise ValueError("AFLNet 消息长度前缀不完整")
        size = int.from_bytes(data[cursor : cursor + 4], sys.byteorder)
        cursor += 4
        if size == 0 or size > 1_000_000 or cursor + size > len(data):
            raise ValueError(f"AFLNet 消息长度无效：{size}")
        messages.append(data[cursor : cursor + size])
        cursor += size
    if not messages:
        raise ValueError("AFLNet 样本不含 SIP 消息")
    return messages


def sample_files(directory: pathlib.Path) -> list[pathlib.Path]:
    if not directory.is_dir():
        return []
    return sorted(
        path for path in directory.iterdir()
        if path.is_file() and path.name.startswith("id:")
    )


def replay(path: pathlib.Path, output: pathlib.Path, idle_timeout: float) -> dict:
    stored = path.read_bytes()
    row = {
        "file": str(path),
        "sha256": hashlib.sha256(stored).hexdigest(),
        "bytes": len(stored),
        "messages": [],
        "startup_seconds": None,
        "server_exit_code": None,
        "port_released": False,
        "connect_error": None,
        "exception": None,
    }
    try:
        messages = decode_aflnet_messages(stored)
    except ValueError as error:
        row["exception"] = str(error)
        return row
    row["message_count"] = len(messages)
    process = None
    log_file = None
    connection = None
    try:
        process, log_file = start_server("gcov", output / "server-logs" / f"{path.name}.log")
        row["startup_seconds"] = round(wait_listener(process), 4)
        connection = socket.create_connection(("127.0.0.1", 5060), timeout=3)
        reader = SIPReader(connection)
        for index, message in enumerate(messages):
            result = {"index": index, "request_bytes": len(message), "response_codes": []}
            connection.sendall(message)
            for response in reader.read_available(idle_timeout, maximum=64):
                code = response_code(response)
                if code is not None:
                    result["response_codes"].append(code)
            row["messages"].append(result)
    except (OSError, RuntimeError, TimeoutError, ValueError) as error:
        if isinstance(error, OSError) and connection is None:
            row["connect_error"] = f"{type(error).__name__}: {error}"
        else:
            row["exception"] = f"{type(error).__name__}: {error}"
    finally:
        if connection is not None:
            connection.close()
        if process is not None:
            row["server_exit_code"] = stop_server(process)
        if log_file is not None:
            log_file.close()
        deadline = time.monotonic() + 2.0
        while time.monotonic() < deadline and not port_is_closed():
            time.sleep(0.05)
        row["port_released"] = port_is_closed()
        import subprocess

        subprocess.run(["/workspace/clean.sh"], check=False)
    return row


def main() -> int:
    parser = argparse.ArgumentParser(description="独立回放 SIP/TCP AFLNet 样本")
    parser.add_argument("--fuzz-dir", required=True, type=pathlib.Path)
    parser.add_argument("--output", required=True, type=pathlib.Path)
    parser.add_argument("--limit", type=int, default=200)
    parser.add_argument("--idle-timeout", type=float, default=0.25)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    groups = {
        "queue": sample_files(args.fuzz_dir / "replayable-queue"),
        "crashes": sample_files(args.fuzz_dir / "replayable-crashes"),
        "hangs": sample_files(args.fuzz_dir / "replayable-hangs"),
    }
    if args.limit > 0:
        groups["queue"] = groups["queue"][: args.limit]
    summary = {}
    for name, files in groups.items():
        rows = []
        destination = args.output / f"{name}-replay.jsonl"
        with destination.open("w", encoding="utf-8") as stream:
            for path in files:
                row = replay(path, args.output, args.idle_timeout)
                rows.append(row)
                stream.write(json.dumps(row, ensure_ascii=False) + "\n")
                stream.flush()
        summary[name] = {
            "sample_count": len(rows),
            "replayed_count": sum(
                row["connect_error"] is None
                and row["exception"] is None
                and row["port_released"]
                for row in rows
            ),
            "abnormal_exit_count": sum(
                row["server_exit_code"] not in (None, 0, -signal.SIGTERM, -signal.SIGKILL)
                for row in rows
            ),
            "response_count": sum(
                len(message["response_codes"])
                for row in rows
                for message in row["messages"]
            ),
            "errors": [
                row for row in rows if row["exception"] or row["connect_error"]
            ],
        }
    report = {
        "replay_mode": "每条样本使用全新 Asterisk/gcov 进程和全新状态目录",
        "queue_limit": args.limit,
        "groups": summary,
    }
    (args.output / "replay-summary.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if summary["queue"]["replayed_count"] > 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
