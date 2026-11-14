"""为 Dovecot IMAP 冒烟验证和语料回放提供公共协议函数。"""

from __future__ import annotations

import os
import re
import socket
import subprocess
import time
from pathlib import Path
from typing import Any

CONFIG = "/workspace/dovecot.conf"
PORT = int(os.environ.get("IMAP_PORT", "1143"))
HOST = "127.0.0.1"
LINE_LIMIT = 1024 * 1024

LITERAL_MARKER = re.compile(rb"\{([0-9]+)\+?\}\r?\n$")


class ImapError(RuntimeError):
    """表示连接或 IMAP 行读取失败。"""


class ImapReader:
    def __init__(self, sock: socket.socket):
        self.sock = sock
        self.stream = sock.makefile("rb")

    def read_line(self) -> bytes:
        line = self.stream.readline(LINE_LIMIT + 1)
        if not line:
            raise ImapError("服务端关闭连接")
        if len(line) > LINE_LIMIT:
            raise ImapError("服务端响应行超出 1 MiB 限制")
        return line

    def greeting(self) -> bytes:
        return self.read_line()

    def response_for_tag(self, tag: bytes) -> tuple[bytes, list[bytes]]:
        response = bytearray()
        lines: list[bytes] = []
        while True:
            line = self.read_line()
            response.extend(line)
            lines.append(line)
            marker = LITERAL_MARKER.search(line)
            if marker is not None:
                length = int(marker.group(1))
                literal = self.stream.read(length)
                if len(literal) != length:
                    raise ImapError("服务端字面量响应被截断")
                response.extend(literal)
            if line.startswith(tag + b" "):
                return bytes(response), lines

    def response_for_continuation(self, tag: bytes) -> tuple[bytes, list[bytes]]:
        response = bytearray()
        lines: list[bytes] = []
        while True:
            line = self.read_line()
            response.extend(line)
            lines.append(line)
            if line.startswith(b"+") or line.startswith(tag + b" "):
                return bytes(response), lines

    def close(self) -> None:
        try:
            self.stream.close()
        except OSError:
            pass


def response_state(line: bytes) -> int:
    line = line.strip(b"\r\n \t")
    if not line:
        return 30
    if line.startswith(b"+"):
        return 20

    fields = line.split(None, 2)
    if fields[0] == b"*":
        if len(fields) < 2:
            return 30
        atom = fields[1]
        if atom[:1].isdigit():
            if len(fields) < 3:
                return 30
            atom = fields[2].split(None, 1)[0]
        if atom.upper() in (b"OK", b"NO", b"BAD", b"BYE"):
            return {b"OK": 1, b"NO": 2, b"BAD": 3, b"BYE": 4}[atom.upper()]
    elif len(fields) >= 2:
        atom = fields[1]
        if atom.upper() in (b"OK", b"NO", b"BAD", b"BYE"):
            return {b"OK": 10, b"NO": 11, b"BAD": 12, b"BYE": 13}[atom.upper()]
    else:
        return 30

    value = 2166136261
    for byte in atom.upper():
        value = ((value ^ byte) * 16777619) & 0xFFFFFFFF
    return 100 + value % 60000


def response_states(lines: list[bytes]) -> list[int]:
    return [response_state(line) for line in lines]


def split_requests(data: bytes) -> list[bytes]:
    regions: list[bytes] = []
    start = 0
    pos = 0
    quoted = False
    escaped = False
    while pos < len(data):
        if not quoted and data[pos] == ord("{"):
            marker = re.match(rb"\{([0-9]+)\+?\}\r\n", data[pos:])
            if marker is not None:
                body_start = pos + marker.end()
                body_length = int(marker.group(1))
                body_end = body_start + body_length
                if body_end > len(data):
                    regions.append(data[start:])
                    return regions
                pos = body_end
                continue
        byte = data[pos]
        if quoted:
            if escaped:
                escaped = False
            elif byte == ord("\\"):
                escaped = True
            elif byte == ord('"'):
                quoted = False
        elif byte == ord('"'):
            quoted = True
        elif byte == ord("\r") and pos + 1 < len(data) and data[pos + 1] == ord("\n"):
            end = pos + 2
            regions.append(data[start:end])
            start = end
            pos = end
            continue
        pos += 1
    if start < len(data):
        regions.append(data[start:])
    return regions


def request_tag(region: bytes) -> bytes:
    first = region.split(None, 1)[0] if region.split(None, 1) else b""
    return first


def replay_data(sock: socket.socket, reader: ImapReader, data: bytes) -> dict[str, Any]:
    greeting = reader.greeting()
    all_states = response_states([greeting])
    response_bytes = len(greeting)
    commands = 0
    timeouts = 0
    errors: list[str] = []
    regions = split_requests(data)

    for region in regions:
        tag = request_tag(region)
        if not tag:
            errors.append("请求区域没有标签")
            break
        try:
            sock.sendall(region)
            response, lines = reader.response_for_tag(tag)
            response_bytes += len(response)
            all_states.extend(response_states(lines))
            commands += 1
        except socket.timeout:
            timeouts += 1
            errors.append("等待标签响应超时")
            break
        except (OSError, ImapError) as exc:
            errors.append(str(exc))
            break

    return {
        "commands": commands,
        "timeouts": timeouts,
        "response_bytes": response_bytes,
        "response_states": all_states,
        "errors": errors,
        "regions": len(regions),
    }


def start_server(variant: str, log_path: Path) -> subprocess.Popen[bytes]:
    env = os.environ.copy()
    prefix_names = {
        "reference": "DOVECOT_REFERENCE_PREFIX",
        "afl": "DOVECOT_AFL_PREFIX",
        "gcov": "DOVECOT_GCOV_PREFIX",
    }
    defaults = {
        "reference": "/home/ubuntu/experiments/dovecot-reference",
        "afl": "/home/ubuntu/experiments/dovecot-afl",
        "gcov": "/home/ubuntu/experiments/dovecot-gcov",
    }
    if variant not in prefix_names:
        raise ValueError(f"未知服务端构建类型：{variant}")
    prefix = env.get(prefix_names[variant], defaults[variant])
    env["DOVECOT_CONFIG"] = CONFIG
    env["PATH"] = f"{prefix}/bin:{prefix}/sbin:{prefix}/libexec:{env.get('PATH', '')}"
    env["LD_LIBRARY_PATH"] = f"{prefix}/lib:{env.get('LD_LIBRARY_PATH', '')}"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_file = log_path.open("wb")
    process = subprocess.Popen(
        ["/workspace/start-server-runtime.sh", variant],
        env=env,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    process._benchmark_log_file = log_file  # type: ignore[attr-defined]
    process._benchmark_stop_command = [  # type: ignore[attr-defined]
        "sudo",
        "-n",
        "/usr/local/sbin/dovecot-root-launcher",
        variant,
        "stop",
    ]
    return process


def stop_server(process: subprocess.Popen[bytes]) -> int:
    if process.poll() is None:
        try:
            stop_command = getattr(process, "_benchmark_stop_command")
            stopped = subprocess.run(
                stop_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
                timeout=8,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ImapError(f"无法调用受限 Dovecot 停止入口：{exc}") from exc
        if stopped.returncode != 0:
            detail = stopped.stdout.decode("utf-8", errors="replace").strip()
            raise ImapError(
                f"Dovecot 停止入口返回 {stopped.returncode}：{detail}"
            )
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired as exc:
            raise ImapError("Dovecot 已收到停止请求，但主进程未在 5 秒内退出") from exc
    log_file = getattr(process, "_benchmark_log_file", None)
    if log_file is not None:
        log_file.close()
    return int(process.returncode or 0)


def wait_until_ready(process: subprocess.Popen[bytes], timeout: float = 12.0) -> None:
    deadline = time.monotonic() + timeout
    last_error = "尚未尝试连接"
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise ImapError(f"服务端提前退出，状态码 {process.returncode}")
        try:
            with socket.create_connection((HOST, PORT), timeout=0.5) as sock:
                sock.settimeout(0.5)
                reader = ImapReader(sock)
                greeting = reader.greeting()
                reader.close()
                if greeting.startswith(b"* OK") or greeting.startswith(b"* PREAUTH"):
                    return
                last_error = f"非预期欢迎行：{greeting!r}"
        except (OSError, ImapError) as exc:
            last_error = str(exc)
        time.sleep(0.05)
    raise ImapError(f"等待 IMAP 监听就绪超时：{last_error}")


def connect_imap(timeout: float = 12.0) -> tuple[socket.socket, ImapReader, bytes]:
    sock = socket.create_connection((HOST, PORT), timeout=timeout)
    sock.settimeout(timeout)
    reader = ImapReader(sock)
    greeting = reader.greeting()
    return sock, reader, greeting


def command_response(sock: socket.socket, reader: ImapReader, tag: str, command: str) -> tuple[bytes, list[bytes]]:
    sock.sendall(f"{tag} {command}\r\n".encode("ascii"))
    return reader.response_for_tag(tag.encode("ascii"))


def append_response(
    sock: socket.socket, reader: ImapReader, tag: str, message: bytes
) -> tuple[bytes, list[bytes]]:
    marker_tag = tag.encode("ascii")
    sock.sendall(f"{tag} APPEND INBOX {{{len(message)}+}}\r\n".encode("ascii") + message + b"\r\n")
    return reader.response_for_tag(marker_tag)


def tagged_status(lines: list[bytes], tag: str) -> str:
    prefix = tag.encode("ascii") + b" "
    for line in lines:
        if line.startswith(prefix):
            parts = line.split(None, 2)
            if len(parts) >= 2:
                return parts[1].decode("ascii", "replace").upper()
    return "MISSING"


def normalize_states(value: dict[str, Any]) -> str:
    return ",".join(str(state) for state in value["response_states"])
