#!/usr/bin/env python3
"""独立启动故障注入探针并回放崩溃样本，保留进程退出和日志证据。"""

import hashlib
import json
import os
import pathlib
import signal
import socket
import struct
import subprocess
import sys
import time


def main() -> int:
    sample = pathlib.Path(sys.argv[1])
    output = pathlib.Path(sys.argv[2])
    binary = pathlib.Path("/home/ubuntu/experiments/fault-probe")
    port = int(os.environ.get("FAULT_PROBE_PORT", "12059"))
    output.mkdir(parents=True, exist_ok=True)
    log_path = output / "fault-probe-replay.log"
    log_file = log_path.open("wb")
    process = subprocess.Popen(
        [str(binary), str(port)],
        stdin=subprocess.DEVNULL,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    abnormal = False
    try:
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError("故障探针在接收回放请求前退出")
            if "等待 NFSv3 RPC 请求".encode("utf-8") in log_path.read_bytes():
                break
            time.sleep(0.05)
        else:
            raise RuntimeError("故障探针没有监听测试端口")

        with socket.create_connection(("127.0.0.1", port), timeout=2) as client:
            encoded = sample.read_bytes()
            offset = 0
            packets = []
            while offset < len(encoded):
                if len(encoded) - offset < 4:
                    raise ValueError("AFLNet 崩溃样本长度前缀不完整")
                packet_size = struct.unpack_from("=I", encoded, offset)[0]
                offset += 4
                if packet_size > len(encoded) - offset:
                    raise ValueError("AFLNet 崩溃样本长度前缀越界")
                packets.append(encoded[offset : offset + packet_size])
                offset += packet_size
            client.sendall(b"".join(packets))
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            pass
        abnormal = process.returncode == -signal.SIGABRT
        report = {
            "probe_binary": str(binary),
            "sample": str(sample),
            "sample_sha256": hashlib.sha256(sample.read_bytes()).hexdigest(),
            "exit_code": process.returncode,
            "signal": -process.returncode if process.returncode is not None and process.returncode < 0 else None,
            "abnormal_exit_observed": abnormal,
            "log": str(log_path),
        }
        (output / "fault-probe-replay.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        if not abnormal:
            raise RuntimeError(f"回放没有复现 SIGABRT：退出码={process.returncode}")
        print(f"通过：独立回放观察到 SIGABRT；证据见 {output}")
        return 0
    finally:
        if process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=2)
        log_file.close()


if __name__ == "__main__":
    raise SystemExit(main())
