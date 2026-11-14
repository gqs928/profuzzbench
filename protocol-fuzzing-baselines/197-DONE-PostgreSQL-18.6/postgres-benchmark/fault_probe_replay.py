#!/usr/bin/env python3
"""独立回放 AFLNet 崩溃样本并验证探针进程退出信号。"""

from __future__ import annotations

import hashlib
import json
import resource
import socket
import subprocess
import sys
import time
from pathlib import Path


def decode_requests(raw: bytes) -> list[bytes]:
    """解析 AFLNet replayable 样本中的小端长度前缀和原始请求。"""
    requests: list[bytes] = []
    offset = 0
    while offset < len(raw):
        if len(raw) - offset < 4:
            raise ValueError("样本末尾缺少完整的请求长度前缀")
        size = int.from_bytes(raw[offset:offset + 4], "little")
        offset += 4
        if size <= 0 or size > len(raw) - offset:
            raise ValueError(f"请求长度前缀无效：{size}")
        requests.append(raw[offset:offset + size])
        offset += size
    if not requests:
        raise ValueError("样本没有可回放的请求")
    return requests


def read_backend_frame(sock: socket.socket) -> bytes:
    """读取一条完整的 PostgreSQL 后端消息。"""
    header = bytearray()
    while len(header) < 5:
        chunk = sock.recv(5 - len(header))
        if not chunk:
            raise ConnectionError("服务端在返回完整消息头前关闭连接")
        header.extend(chunk)
    body_size = int.from_bytes(header[1:5], "big") - 4
    if body_size < 0:
        raise ValueError("服务端返回了无效的 PostgreSQL 消息长度")
    body = bytearray()
    while len(body) < body_size:
        chunk = sock.recv(body_size - len(body))
        if not chunk:
            raise ConnectionError("服务端在返回完整消息体前关闭连接")
        body.extend(chunk)
    return bytes(header + body)


def main() -> int:
    if len(sys.argv) != 5:
        print("用法：fault_probe_replay.py 样本 服务端 端口 输出目录", file=sys.stderr)
        return 2
    sample = Path(sys.argv[1])
    server_path = Path(sys.argv[2])
    port = int(sys.argv[3])
    output = Path(sys.argv[4])
    output.mkdir(parents=True, exist_ok=True)
    raw = sample.read_bytes()
    try:
        requests = decode_requests(raw)
    except ValueError as exc:
        print(f"无法解析 AFLNet 样本：{exc}", file=sys.stderr)
        return 2
    log_path = output / "server.log"
    def disable_core_dump() -> None:
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))

    with log_path.open("wb") as log:
        server = subprocess.Popen(
            [str(server_path), str(port)], stdout=log, stderr=subprocess.STDOUT,
            start_new_session=True, preexec_fn=disable_core_dump,
        )
        connected = False
        last_error = None
        for _ in range(200):
            if server.poll() is not None:
                break
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            try:
                sock.connect(("127.0.0.1", port))
                connected = True
                last_error = None
                for request in requests:
                    sock.sendall(request)
                    if request[:1] == b"\x00":
                        startup_responses = []
                        while not startup_responses or startup_responses[-1][:1] != b"Z":
                            startup_responses.append(read_backend_frame(sock))
                    elif request[:1] == b"Q":
                        # 查询故意触发崩溃；服务端不需要再返回响应。
                        break
                break
            except OSError as exc:
                last_error = str(exc)
                sock.close()
                time.sleep(0.025)
        try:
            return_code = server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.terminate()
            try:
                return_code = server.wait(timeout=1)
            except subprocess.TimeoutExpired:
                server.kill()
                return_code = server.wait(timeout=1)
    report = {
        "sample": str(sample),
        "sample_bytes": len(raw),
        "request_count": len(requests),
        "request_sizes": [len(request) for request in requests],
        "sample_sha256": hashlib.sha256(raw).hexdigest(),
        "server": str(server_path),
        "endpoint": f"tcp://127.0.0.1:{port}",
        "connected_and_replayed": connected,
        "server_exit_code": return_code,
        "server_exit_signal": -return_code if return_code < 0 else None,
        "expected_sigabrt": return_code == -6,
        "last_connect_error": last_error,
        "server_log": str(log_path),
    }
    (output / "replay.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report["connected_and_replayed"] and report["expected_sigabrt"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
