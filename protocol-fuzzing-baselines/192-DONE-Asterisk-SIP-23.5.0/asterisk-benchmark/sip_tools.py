#!/usr/bin/env python3
"""SIP/TCP 回放工具，统一消息分帧、响应读取和进程复位逻辑。"""

from __future__ import annotations

import os
import pathlib
import signal
import socket
import subprocess
import time


def message_size(buffer: bytearray) -> int | None:
    """从接收缓冲区计算一条 SIP 消息长度；头部未收完整时返回 None。"""
    boundary = buffer.find(b"\r\n\r\n")
    delimiter_size = 4
    if boundary < 0:
        boundary = buffer.find(b"\n\n")
        delimiter_size = 2
    if boundary < 0:
        return None
    body_start = boundary + delimiter_size
    header = bytes(buffer[:boundary]).splitlines()
    content_length = 0
    for line in header[1:]:
        if b":" not in line:
            continue
        name, value = line.split(b":", 1)
        if name.strip().lower() in (b"content-length", b"l"):
            parsed = value.strip()
            if not parsed.isdigit():
                raise ValueError("响应中的 Content-Length 不是十进制整数")
            content_length = int(parsed)
    return body_start + content_length


def response_code(message: bytes) -> int | None:
    """提取 SIP 响应首行的三位状态码。"""
    first_line = message.split(b"\n", 1)[0].strip()
    pieces = first_line.split()
    if len(pieces) < 2 or not pieces[0].startswith(b"SIP/"):
        return None
    if len(pieces[1]) != 3 or not pieces[1].isdigit():
        return None
    return int(pieces[1])


class SIPReader:
    """读取 TCP 字节流并保留一次 recv 中多到的下一条消息。"""

    def __init__(self, connection: socket.socket):
        self.connection = connection
        self.buffer = bytearray()

    def read_one(self, timeout: float) -> bytes | None:
        deadline = time.monotonic() + timeout
        while True:
            total = message_size(self.buffer)
            if total is not None and len(self.buffer) >= total:
                message = bytes(self.buffer[:total])
                del self.buffer[:total]
                return message
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise socket.timeout("等待 SIP 响应超时")
            self.connection.settimeout(remaining)
            chunk = self.connection.recv(65536)
            if not chunk:
                if self.buffer:
                    raise ConnectionError("服务端关闭连接时留下不完整 SIP 响应")
                return None
            self.buffer.extend(chunk)
            if len(self.buffer) > 1_000_000:
                raise ValueError("服务端响应超过单条 1 MB 上限")

    def read_available(self, idle_timeout: float, maximum: int = 16) -> list[bytes]:
        messages = []
        while len(messages) < maximum:
            try:
                message = self.read_one(idle_timeout)
            except socket.timeout:
                break
            if message is None:
                break
            messages.append(message)
        return messages


def sip_request(
    method: str,
    target: str,
    call_id: str,
    cseq: int,
    branch: str,
    from_tag: str,
    body: bytes = b"",
    extra_headers: tuple[tuple[str, str], ...] = (),
) -> bytes:
    """按确定的头顺序生成单条 SIP 请求，正文长度由字节数计算。"""
    rows = [
        f"{method} {target} SIP/2.0",
        f"Via: SIP/2.0/TCP 127.0.0.1:5061;branch={branch};rport",
        "Max-Forwards: 70",
        f"From: <sip:alice@127.0.0.1>;tag={from_tag}",
        f"To: <{target}>",
        f"Call-ID: {call_id}",
        f"CSeq: {cseq} {method}",
        "Contact: <sip:alice@127.0.0.1:5061;transport=tcp>",
        "User-Agent: Asterisk-SIP-Fuzz-Benchmark",
    ]
    rows.extend(f"{name}: {value}" for name, value in extra_headers)
    if body and not any(name.lower() == "content-type" for name, _ in extra_headers):
        rows.append("Content-Type: application/sdp")
    rows.append(f"Content-Length: {len(body)}")
    return ("\r\n".join(rows) + "\r\n\r\n").encode("ascii") + body


def smoke_flow(run_id: str) -> dict[str, bytes]:
    """构造 OPTIONS、REGISTER、INVITE/CANCEL 的标准业务流程。"""
    call_id = f"smoke-{run_id}@127.0.0.1"
    options = sip_request(
        "OPTIONS", "sip:100@127.0.0.1", f"options-{run_id}@127.0.0.1", 1,
        f"z9hG4bK-options-{run_id}", f"options-{run_id}",
    )
    register = sip_request(
        "REGISTER", "sip:alice@127.0.0.1", f"register-{run_id}@127.0.0.1", 1,
        f"z9hG4bK-register-{run_id}", f"register-{run_id}",
        extra_headers=(("Expires", "300"),),
    )
    sdp = (
        b"v=0\r\n"
        + b"o=alice 1 1 IN IP4 127.0.0.1\r\n"
        + b"s=Smoke SIP call\r\n"
        + b"c=IN IP4 127.0.0.1\r\n"
        + b"t=0 0\r\n"
        + b"m=audio 4000 RTP/AVP 0\r\n"
        + b"a=rtpmap:0 PCMU/8000\r\n"
    )
    invite = sip_request(
        "INVITE", "sip:100@127.0.0.1", call_id, 2,
        f"z9hG4bK-dialog-{run_id}", f"dialog-{run_id}", sdp,
        extra_headers=(("Allow", "INVITE, ACK, CANCEL, BYE, OPTIONS"),),
    )
    cancel = sip_request(
        "CANCEL", "sip:100@127.0.0.1", call_id, 2,
        f"z9hG4bK-dialog-{run_id}", f"dialog-{run_id}",
    )
    return {"options": options, "register": register, "invite": invite, "cancel": cancel}


def start_server(variant: str, log_path: pathlib.Path) -> tuple[subprocess.Popen, object]:
    """启动指定变体的前台 Asterisk，并把本轮日志写入独立文件。"""
    cleanup = pathlib.Path("/workspace/clean.sh")
    environment = os.environ.copy()
    environment["ASTERISK_VARIANT"] = variant
    subprocess.run([str(cleanup)], check=True, env=environment)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_file = log_path.open("wb")
    environment["ASTERISK_VARIANT"] = variant
    environment["ASTERISK_RUN_ROOT"] = "/tmp/asterisk-run"
    environment["ASAN_OPTIONS"] = environment.get(
        "ASAN_OPTIONS", "abort_on_error=1:symbolize=0:detect_leaks=0"
    )
    process = subprocess.Popen(
        ["/workspace/start-server.sh"],
        stdin=subprocess.DEVNULL,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        start_new_session=True,
        env=environment,
    )
    return process, log_file


def wait_listener(process: subprocess.Popen, timeout: float = 15.0) -> float:
    """等待回环 SIP/TCP 端口就绪，并返回从启动到就绪的秒数。"""
    started = time.monotonic()
    deadline = started + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"Asterisk 在监听就绪前退出，exit={process.returncode}")
        try:
            with socket.create_connection(("127.0.0.1", 5060), timeout=0.2):
                return time.monotonic() - started
        except OSError:
            time.sleep(0.05)
    raise TimeoutError("Asterisk 没有在 15 秒内监听 TCP/5060")


def wait_server_ready(variant: str, timeout: float = 15.0) -> float:
	"""等待核心模块、PJSIP endpoint 和拨号计划全部就绪。"""
	prefixes = {
		"reference": "/home/ubuntu/asterisk-reference",
		"afl": "/home/ubuntu/asterisk-afl",
		"gcov": "/home/ubuntu/asterisk-gcov",
	}
	prefix = prefixes[variant]
	environment = os.environ.copy()
	environment["LD_LIBRARY_PATH"] = f"{prefix}/lib:" + environment.get("LD_LIBRARY_PATH", "")
	started = time.monotonic()
	commands = (
		("core waitfullybooted", "fully booted"),
		("pjsip show endpoint alice", "Endpoint:  alice"),
		("dialplan show fuzz", "'100' =>"),
	)
	for command, expected in commands:
		result = subprocess.run(
			[
				f"{prefix}/sbin/asterisk",
				"-C", "/tmp/asterisk-run/asterisk.conf",
				"-rx", command,
			],
			capture_output=True,
			text=True,
			env=environment,
			timeout=timeout,
			check=False,
		)
		if result.returncode != 0 or expected not in result.stdout:
			raise RuntimeError(
				f"Asterisk 未就绪（{command}）：{result.stdout.strip()} {result.stderr.strip()}"
			)
	return time.monotonic() - started


def stop_server(process: subprocess.Popen, timeout: float = 8.0) -> int | None:
    """结束服务进程并等待 gcov/日志刷新。"""
    if process.poll() is None:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=3)
    return process.returncode


def port_is_closed(timeout: float = 0.25) -> bool:
    """确认上一轮进程退出后端口已释放。"""
    try:
        with socket.create_connection(("127.0.0.1", 5060), timeout=timeout):
            return False
    except OSError:
        return True
