#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path


def main() -> int:
    if len(sys.argv) not in (3, 4):
        print("usage: replay_hang.py SAMPLE LOG [reference|afl]", file=sys.stderr)
        return 2
    sample = Path(sys.argv[1]).read_bytes()
    log_path = Path(sys.argv[2])
    variant = sys.argv[3] if len(sys.argv) == 4 else "reference"
    if variant not in {"reference", "afl"}:
        print(f"unsupported target variant: {variant}", file=sys.stderr)
        return 2
    target_root = f"/home/ubuntu/experiments/mosquitto-{variant}"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = f"{target_root}/lib"

    with log_path.open("wb") as log:
        broker = subprocess.Popen(
            [
                f"{target_root}/src/mosquitto",
                "-c",
                "/workspace/mosquitto.conf",
            ],
            stdout=log,
            stderr=subprocess.STDOUT,
            env=env,
            start_new_session=True,
        )
        connected = False
        response_bytes = 0
        client_read_result = "not_connected"
        error = ""
        try:
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                if broker.poll() is not None:
                    error = f"broker exited before listen: {broker.returncode}"
                    break
                try:
                    with socket.create_connection(("127.0.0.1", 1883), timeout=0.25) as sock:
                        connected = True
                        sock.settimeout(2)
                        sock.sendall(sample)
                        try:
                            response = sock.recv(65536)
                            response_bytes = len(response)
                            client_read_result = "data" if response else "peer_closed"
                        except socket.timeout:
                            client_read_result = "timeout_no_data"
                    break
                except OSError:
                    time.sleep(0.05)
            if not connected and not error:
                error = "broker did not listen within 10 seconds"
            time.sleep(2)
            status = "broker_alive_after_input" if broker.poll() is None else "broker_exited_after_input"
        finally:
            if broker.poll() is None:
                broker.send_signal(signal.SIGTERM)
                try:
                    broker.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    broker.kill()
                    broker.wait(timeout=5)

    report = {
        "sample_bytes": len(sample),
        "target_variant": variant,
        "broker_listened": connected,
        "response_bytes": response_bytes,
        "client_read_result": client_read_result,
        "status": status,
        "broker_returncode_after_shutdown": broker.returncode,
        "error": error,
        "broker_log": str(log_path),
    }
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
