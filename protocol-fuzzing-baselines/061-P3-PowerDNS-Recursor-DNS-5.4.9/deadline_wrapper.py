#!/usr/bin/env python3
"""Run a command for a bounded time and repeat SIGINT until it exits cleanly."""
from __future__ import annotations

import json
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path


def seconds(value: str) -> float:
    match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)(s|m|h|d)?", value)
    if not match:
        raise ValueError(f"invalid duration: {value!r}")
    scale = {None: 1, "s": 1, "m": 60, "h": 3600, "d": 86400}[match.group(2)]
    result = float(match.group(1)) * scale
    if result <= 0:
        raise ValueError("duration must be positive")
    return result


def write_status(path: Path, data: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    if len(sys.argv) < 4:
        print("usage: deadline_wrapper.py DURATION STATUS_JSON COMMAND [ARG ...]", file=sys.stderr)
        return 2
    duration = seconds(sys.argv[1])
    status_path = Path(sys.argv[2])
    command = sys.argv[3:]
    process = subprocess.Popen(command, start_new_session=True)
    deadline = time.monotonic() + duration
    while process.poll() is None and time.monotonic() < deadline:
        time.sleep(min(0.25, max(0.01, deadline - time.monotonic())))
    if process.poll() is not None:
        write_status(status_path, {"deadline_reached": False, "stop_method": "natural",
                                   "return_code": process.returncode, "sigint_attempts": 0})
        return int(process.returncode)

    attempts = 0
    for attempts in range(1, 16):
        try:
            os.killpg(process.pid, signal.SIGINT)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=1)
            write_status(status_path, {"deadline_reached": True, "stop_method": "SIGINT",
                                       "return_code": process.returncode,
                                       "sigint_attempts": attempts})
            return 124
        except subprocess.TimeoutExpired:
            continue

    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        process.wait(timeout=10)
        write_status(status_path, {"deadline_reached": True, "stop_method": "SIGTERM",
                                   "return_code": process.returncode,
                                   "sigint_attempts": attempts})
        return 125
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait()
        write_status(status_path, {"deadline_reached": True, "stop_method": "SIGKILL",
                                   "return_code": process.returncode,
                                   "sigint_attempts": attempts})
        return 125


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, TimeoutError, ValueError) as exc:
        print(f"deadline wrapper failed: {exc}", file=sys.stderr)
        raise SystemExit(2)
