#!/usr/bin/env python3
"""Run one fuzzer for a bounded active duration and record shutdown evidence."""
from __future__ import annotations

import datetime as dt
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path


def parse_duration(value: str) -> float:
    units = {"s": 1, "m": 60, "h": 3600}
    if len(value) < 2 or value[-1] not in units or not value[:-1].isdigit():
        raise ValueError(f"duration must look like 60s, 30m, or 1h: {value}")
    return int(value[:-1]) * units[value[-1]]


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def signal_group(proc: subprocess.Popen[bytes], sig: signal.Signals) -> bool:
    try:
        os.killpg(proc.pid, sig)
        return True
    except ProcessLookupError:
        return False


def main() -> int:
    if len(sys.argv) < 4:
        raise SystemExit("usage: deadline_wrapper.py DURATION OUTPUT.json COMMAND [ARG ...]")
    duration_text, output_name, *command = sys.argv[1:]
    duration = parse_duration(duration_text)
    output = Path(output_name)
    output.parent.mkdir(parents=True, exist_ok=True)
    start_utc = utc_now()
    start_mono = time.monotonic()
    deadline = start_mono + duration
    proc = subprocess.Popen(command, start_new_session=True)
    stop_method = "natural-exit"
    attempts: list[dict[str, object]] = []
    deadline_reached = False
    try:
        while proc.poll() is None and time.monotonic() < deadline:
            time.sleep(min(0.5, max(0.01, deadline - time.monotonic())))
        if proc.poll() is None:
            deadline_reached = True
            for sig, wait_seconds in ((signal.SIGINT, 8), (signal.SIGINT, 5),
                                      (signal.SIGTERM, 3), (signal.SIGKILL, 2)):
                sent = signal_group(proc, sig)
                attempts.append({"signal": sig.name, "sent": sent, "wait_seconds": wait_seconds})
                try:
                    proc.wait(timeout=wait_seconds)
                    stop_method = sig.name
                    break
                except subprocess.TimeoutExpired:
                    continue
        return_code = proc.wait(timeout=3)
    except BaseException:
        if proc.poll() is None:
            signal_group(proc, signal.SIGTERM)
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                signal_group(proc, signal.SIGKILL)
                proc.wait(timeout=2)
        raise
    elapsed = time.monotonic() - start_mono
    result = {
        "command": command,
        "requested_duration_seconds": duration,
        "start_time_utc": start_utc,
        "end_time_utc": utc_now(),
        "elapsed_seconds": round(elapsed, 3),
        "deadline_reached": deadline_reached,
        "stop_method": stop_method,
        "stop_attempts": attempts,
        "child_return_code": return_code,
        "wrapper_exit_code": 124 if deadline_reached else return_code,
    }
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)
    return int(result["wrapper_exit_code"])


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as exc:
        print(f"deadline wrapper failed: {exc}", file=sys.stderr)
        raise SystemExit(2)
