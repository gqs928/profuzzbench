#!/usr/bin/env python3
"""验证普通 UDP 与长连接 RADIUS/TCP 的真实认证和记账响应。"""

import hashlib
import json
import os
import pathlib
import signal
import socket
import subprocess
import sys
import time

from prepare_seeds import SECRET, access, accounting


WORKDIR = pathlib.Path(os.environ.get("WORKDIR", "/home/ubuntu/experiments"))
PORT = int(os.environ.get("PORT", "1812"))
ACCOUNTING_PORT = int(os.environ.get("ACCOUNTING_PORT", "1813"))


def read_exact(sock: socket.socket, count: int) -> bytes:
    data = bytearray()
    while len(data) < count:
        part = sock.recv(count - len(data))
        if not part:
            raise RuntimeError(f"响应在 {count} 字节前关闭连接")
        data.extend(part)
    return bytes(data)


def receive_packet(sock: socket.socket) -> bytes:
    header = read_exact(sock, 4)
    length = int.from_bytes(header[2:4], "big")
    if length < 20:
        raise RuntimeError(f"服务端返回非法 RADIUS 长度：{length}")
    return header + read_exact(sock, length - 4)


def verify_response(request: bytes, response: bytes, expected_code: int) -> None:
    if len(response) < 20 or int.from_bytes(response[2:4], "big") != len(response):
        raise RuntimeError("响应长度与 RADIUS 头部不一致")
    if response[0] != expected_code or response[1] != request[1]:
        raise RuntimeError(
            f"期望 Code/ID={expected_code}/{request[1]}，实际为 {response[0]}/{response[1]}"
        )
    signed = response[:4] + request[4:20] + response[20:] + SECRET
    if hashlib.md5(signed).digest() != response[4:20]:
        raise RuntimeError("RADIUS 响应认证器校验失败")


def exchange_udp(port: int, request: bytes, code: int) -> bytes:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(3)
        sock.sendto(request, ("127.0.0.1", port))
        response, _ = sock.recvfrom(65535)
    verify_response(request, response, code)
    return response


def start_server(variant: str, session: int, log_dir: pathlib.Path):
    binary = pathlib.Path(os.environ[f"RADIUS_{variant.upper()}_BIN"])
    config = pathlib.Path(os.environ[f"RADIUS_{variant.upper()}_CONFIG"])
    log_path = log_dir / f"server-{variant}-{session:02d}.log"
    log_file = log_path.open("wb")
    command = [str(binary), "-f", "-l", "/dev/null", "-d", str(config)]
    process = subprocess.Popen(
        command,
        stdin=subprocess.DEVNULL,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        if process.poll() is not None:
            log_file.close()
            detail = log_path.read_text(errors="replace")[-8000:]
            raise RuntimeError(f"{variant} 服务端启动失败，退出码={process.returncode}\n{detail}")
        try:
            probe = socket.create_connection(("127.0.0.1", PORT), timeout=0.2)
            probe.close()
            return process, log_file, log_path, command
        except OSError:
            time.sleep(0.1)
    stop_server(process, log_file)
    detail = log_path.read_text(errors="replace")[-8000:]
    raise RuntimeError(f"{variant} TCP/{PORT} 未就绪\n{detail}")


def stop_server(process: subprocess.Popen, log_file) -> None:
    if process.poll() is None:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=5)
    log_file.close()


def run_session(variant: str, session: int, log_dir: pathlib.Path) -> dict:
    subprocess.run(["/workspace/clean.sh"], check=True)
    process, log_file, log_path, command = start_server(variant, session, log_dir)
    try:
        udp_requests = [
            ("pap-accept", access(1, b"wonderland"), 2, PORT),
            ("pap-reject", access(2, b"wrong-password"), 3, PORT),
            ("accounting-start", accounting(3, 1), 5, ACCOUNTING_PORT),
            ("accounting-stop", accounting(4, 2), 5, ACCOUNTING_PORT),
        ]
        udp_responses = []
        response_records = []
        for name, request, code, port in udp_requests:
            response = exchange_udp(port, request, code)
            udp_responses.append(response)
            response_records.append(
                {
                    "step": name,
                    "transport": f"udp/{port}",
                    "request_id": request[1],
                    "request_sha256": hashlib.sha256(request).hexdigest(),
                    "expected_response_code": code,
                    "actual_response_code": response[0],
                    "response_sha256": hashlib.sha256(response).hexdigest(),
                }
            )

        tcp_steps = [
            ("pap-accept", access(5, b"wonderland"), 2),
            ("accounting-start", accounting(6, 1), 5),
            ("accounting-stop", accounting(7, 2), 5),
            ("pap-reject", access(8, b"wrong-password"), 3),
            ("pap-retry-accept", access(9, b"wonderland"), 2),
        ]
        tcp_requests = [request for _, request, _ in tcp_steps]
        expected_by_id = {
            request[1]: (name, request, code)
            for name, request, code in tcp_steps
        }
        tcp_by_id = {}
        with socket.create_connection(("127.0.0.1", PORT), timeout=3) as sock:
            sock.settimeout(3)
            sock.sendall(b"".join(tcp_requests))
            for _ in tcp_requests:
                response = receive_packet(sock)
                if response[1] not in expected_by_id:
                    raise RuntimeError(f"服务端返回未知 RADIUS Identifier：{response[1]}")
                name, request, code = expected_by_id[response[1]]
                verify_response(request, response, code)
                tcp_by_id[response[1]] = response
                response_records.append(
                    {
                        "step": name,
                        "transport": f"tcp/{PORT}",
                        "request_id": request[1],
                        "request_sha256": hashlib.sha256(request).hexdigest(),
                        "expected_response_code": code,
                        "actual_response_code": response[0],
                        "response_sha256": hashlib.sha256(response).hexdigest(),
                    }
                )
        tcp_responses = [tcp_by_id[request[1]] for request in tcp_requests]
        response_records.sort(key=lambda row: (row["transport"], row["request_id"]))

        all_responses = udp_responses + tcp_responses
        result = {
            "variant": variant,
            "session": session,
            "command": command,
            "udp_codes": [packet[0] for packet in udp_responses],
            "tcp_codes": [packet[0] for packet in tcp_responses],
            "udp_packets": len(udp_responses),
            "tcp_packets": len(tcp_responses),
            "transcript_sha256": hashlib.sha256(b"".join(all_responses)).hexdigest(),
            "transcript_bytes": sum(map(len, all_responses)),
            "server_exit_code": None,
            "server_log": str(log_path),
            "replay_command": "python3 /workspace/protocol_smoke.py /results/protocol-smoke 10",
            "response_records": response_records,
        }
        return result
    finally:
        stop_server(process, log_file)


def main() -> int:
    output = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "/results/protocol-smoke")
    repetitions = int(sys.argv[2] if len(sys.argv) > 2 else os.environ.get("RADIUS_SMOKE_REPETITIONS", "10"))
    if repetitions < 10:
        raise SystemExit("验收要求同种子至少独立回放 10 次")
    output.mkdir(parents=True, exist_ok=True)
    results = []
    for variant in ("reference", "afl"):
        for session in range(1, repetitions + 1):
            results.append(run_session(variant, session, output))

    reference = {item["transcript_sha256"] for item in results if item["variant"] == "reference"}
    instrumented = {item["transcript_sha256"] for item in results if item["variant"] == "afl"}
    if len(reference) != 1 or len(instrumented) != 1 or reference != instrumented:
        raise RuntimeError("参考版和插桩版的重复业务 transcript 不稳定或不一致")
    for item in results:
        if item["udp_codes"] != [2, 3, 5, 5] or item["tcp_codes"] != [2, 5, 5, 3, 2]:
            raise RuntimeError(f"业务响应不完整：{item}")
    report = {
        "repetitions_per_variant": repetitions,
        "variants": ["reference", "afl"],
        "normal_udp_flow": ["Access-Accept", "Access-Reject", "Accounting-Response x2"],
        "persistent_tcp_flow": ["Access-Accept", "Accounting-Response x2", "Access-Reject", "Access-Accept"],
        "transcript_sha256": next(iter(reference)),
        "sessions": results,
    }
    (output / "protocol-smoke.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"通过：参考版与插桩版各 {repetitions} 次，UDP/TCP 认证和记账响应一致；"
        f"transcript_sha256={report['transcript_sha256']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
