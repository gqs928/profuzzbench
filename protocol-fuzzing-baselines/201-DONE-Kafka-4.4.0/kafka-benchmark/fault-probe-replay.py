#!/usr/bin/env python3
"""单独启动临时异常探针，确认 AFL 保存的样本能令其再次崩溃。"""

from __future__ import annotations

import signal
import socket
import subprocess
import sys
import time
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 4:
        print("用法：fault-probe-replay.py 服务端 样本 输出目录", file=sys.stderr)
        return 2
    target, sample, output = map(Path, sys.argv[1:])
    data = sample.read_bytes()
    log_path = output / "independent-replay.log"
    with log_path.open("wb") as log:
        process = subprocess.Popen([str(target)], stdout=log, stderr=subprocess.STDOUT)
        try:
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    raise RuntimeError("探针在收到样本前退出")
                try:
                    with socket.create_connection(("127.0.0.1", 19092), timeout=0.2) as sock:
                        sock.sendall(data)
                    break
                except OSError:
                    time.sleep(0.05)
            else:
                raise RuntimeError("临时故障探针未监听 19092")
            try:
                status = process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.send_signal(signal.SIGTERM)
                process.wait(timeout=5)
                raise RuntimeError("保存的异常样本没有触发探针崩溃")
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=5)
    (output / "probe-status.txt").write_text(
        f"independent_replay_exit={status}\n"
        "expected_exit=-6 (SIGABRT)\n"
        "temporary_injection_removed=true\n"
        "probe_scope=isolated test-only TCP process; Kafka source unchanged\n",
        encoding="utf-8")
    if status != -signal.SIGABRT:
        raise RuntimeError(f"独立回放退出状态不符合预期：{status}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError) as exc:
        print(f"FAIL：{exc}", file=sys.stderr)
        raise SystemExit(1)
