#!/usr/bin/env python3
"""Replay UDP queue samples against fresh ngtcp2 server processes."""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import signal
import socket
import subprocess
import time
from collections import Counter


def command() -> list[str]:
    return [
        os.environ.get("NGTCP2_SERVER", "/opt/benchmark/osslserver"),
        "127.0.0.1",
        str(int(os.environ.get("NGTCP2_PORT", "4433"))),
        os.environ.get("NGTCP2_KEY", "/opt/benchmark/server.key"),
        os.environ.get("NGTCP2_CERT", "/opt/benchmark/server.crt"),
    ]


def port_bound(port: int) -> bool:
    port_hex = f"{port:04X}"
    for table in (pathlib.Path("/proc/net/udp"), pathlib.Path("/proc/net/udp6")):
        try:
            lines = table.read_text().splitlines()[1:]
        except OSError:
            continue
        for line in lines:
            fields = line.split()
            if len(fields) > 1 and fields[1].rsplit(":", 1)[-1].upper() == port_hex:
                return True
    return False


def wait_bound(proc: subprocess.Popen[bytes], port: int, timeout: float) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            return False
        if port_bound(port):
            return True
        time.sleep(0.01)
    return False


def header_kind(data: bytes) -> str:
    if not data:
        return "empty"
    if not data[0] & 0x80:
        return "short"
    if len(data) < 7:
        return "truncated-long"
    version = int.from_bytes(data[1:5], "big")
    if version == 0:
        return "version-negotiation"
    return f"long-v{version:08x}-type-{(data[0] >> 4) & 3}"


def replay(path: pathlib.Path, port: int, timeout: float) -> dict[str, object]:
    data = path.read_bytes()
    proc = subprocess.Popen(command(), stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL, start_new_session=True)
    row: dict[str, object] = {"file": path.name, "bytes": len(data)}
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client.settimeout(timeout)
    response = b""
    started = wait_bound(proc, port, 3)
    if started:
        try:
            client.sendto(data, ("127.0.0.1", port))
            response, _ = client.recvfrom(65535)
        except socket.timeout:
            pass
        except OSError as exc:
            row["transport_error"] = f"{type(exc).__name__}: {exc}"
    alive = proc.poll() is None
    if alive:
        proc.send_signal(signal.SIGTERM)
    try:
        exit_code = proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        proc.kill()
        exit_code = proc.wait(timeout=2)
    client.close()
    released = not port_bound(port)
    row.update({
        "target_started": started,
        "target_exit_before_cleanup": None if alive else proc.returncode,
        "target_alive_after_input": alive,
        "controlled_exit_code": exit_code,
        "clean_sigterm_exit": alive and exit_code in (0, -signal.SIGTERM),
        "listener_released": released,
        "response_bytes": len(response),
        "response_header_type": header_kind(response),
    })
    return row


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("queue", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    parser.add_argument("--port", type=int, default=int(os.environ.get("NGTCP2_PORT", "4433")))
    parser.add_argument("--response-timeout", type=float, default=0.05)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--allow-target-exit", action="store_true")
    args = parser.parse_args()
    paths = sorted(path for path in args.queue.iterdir()
                   if path.is_file() and not path.name.startswith("."))
    if args.limit is not None:
        paths = paths[:args.limit]
    rows = [replay(path, args.port, args.response_timeout) for path in paths]
    summary = {
        "queue": str(args.queue),
        "samples_total": len(rows),
        "target_started": sum(bool(row["target_started"]) for row in rows),
        "target_alive_after_input": sum(bool(row["target_alive_after_input"]) for row in rows),
        "clean_sigterm_exit": sum(bool(row["clean_sigterm_exit"]) for row in rows),
        "unexpected_exit_before_cleanup": sum(not bool(row["target_alive_after_input"]) for row in rows),
        "listeners_released": sum(bool(row["listener_released"]) for row in rows),
        "no_response": sum(int(row["response_bytes"]) == 0 for row in rows),
        "response_header_types": dict(Counter(str(row["response_header_type"]) for row in rows)),
        "records": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in summary.items() if key != "records"}, indent=2))
    if any(not row["target_started"] or not row["listener_released"] or
           (not args.allow_target_exit and
            (not row["target_alive_after_input"] or not row["clean_sigterm_exit"]))
           for row in rows):
        raise SystemExit("queue replay found a crash, stuck process, or unreleased UDP listener")


if __name__ == "__main__":
    main()
