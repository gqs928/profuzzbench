#!/usr/bin/env python3
"""Replay an AFLNet HTTP/2 queue using one fresh Apache process per sample."""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import signal
import socket
import subprocess
import tempfile
import time
from collections import Counter

PREFACE = b"PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n"


def split_regions(data: bytes) -> tuple[list[bytes], bool, int, int]:
    if not data:
        return [], False, 0, 0
    if not data.startswith(PREFACE):
        return [data], False, 0, len(data)
    offset = len(PREFACE)
    regions: list[bytes] = []
    frames = 0
    malformed_bytes = 0
    if len(data) - offset >= 9:
        size = int.from_bytes(data[offset:offset + 3], "big")
        end = offset + 9 + size
        stream_id = int.from_bytes(data[offset + 5:offset + 9], "big") & 0x7FFFFFFF
        if (data[offset + 3] == 4 and data[offset + 4] == 0 and stream_id == 0
                and size % 6 == 0 and end <= len(data)):
            regions.append(data[:end])
            frames += 1
            offset = end
        else:
            regions.append(PREFACE)
    else:
        regions.append(PREFACE)
    while offset < len(data):
        if len(data) - offset < 9:
            malformed_bytes = len(data) - offset
            regions.append(data[offset:])
            break
        size = int.from_bytes(data[offset:offset + 3], "big")
        end = offset + 9 + size
        if end > len(data):
            malformed_bytes = len(data) - offset
            regions.append(data[offset:])
            break
        regions.append(data[offset:end])
        frames += 1
        offset = end
    return regions, True, frames, malformed_bytes


def response_frame_types(data: bytes) -> list[int]:
    types = []
    offset = 0
    while len(data) - offset >= 9:
        size = int.from_bytes(data[offset:offset + 3], "big")
        if offset + 9 + size > len(data):
            break
        types.append(data[offset + 3])
        offset += 9 + size
    return types


def wait_listener(proc: subprocess.Popen[bytes], port: int, timeout: float) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            return False
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                return True
        except OSError:
            time.sleep(0.05)
    return False


def terminate(proc: subprocess.Popen[bytes]) -> int | None:
    if proc.poll() is not None:
        return proc.returncode
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except ProcessLookupError:
        return proc.poll()
    try:
        proc.wait(timeout=2)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        proc.wait(timeout=2)
    return proc.returncode


def replay(path: pathlib.Path, port: int, response_timeout: float) -> dict[str, object]:
    data = path.read_bytes()
    regions, preface_valid, complete_frames, malformed_bytes = split_regions(data)
    row: dict[str, object] = {
        "file": path.name, "size": len(data), "preface_valid": preface_valid,
        "complete_request_frames": complete_frames, "malformed_tail_bytes": malformed_bytes,
    }
    pathlib.Path("/tmp/httpd-benchmark.pid").unlink(missing_ok=True)
    pathlib.Path("/tmp/httpd-benchmark.pid.lock").unlink(missing_ok=True)
    with tempfile.TemporaryFile() as log:
        proc = subprocess.Popen(["/opt/benchmark/target.sh"], stdout=subprocess.DEVNULL,
                                stderr=log, start_new_session=True)
        try:
            if not wait_listener(proc, port, 3.0):
                row.update({"target_started": False, "target_exit_code": proc.poll(),
                            "transport_error": "listener_not_ready"})
                return row
            response = bytearray()
            peer_closed = False
            transport_error = None
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=1.0) as sock:
                    sock.settimeout(response_timeout)
                    for region in regions:
                        if not region:
                            continue
                        sock.sendall(region)
                        while True:
                            try:
                                chunk = sock.recv(65536)
                            except socket.timeout:
                                break
                            if not chunk:
                                peer_closed = True
                                break
                            response.extend(chunk)
                        if peer_closed:
                            break
            except OSError as exc:
                transport_error = f"{type(exc).__name__}: {exc}"
            time.sleep(0.05)
            row.update({"target_started": True, "regions_sent": len(regions),
                        "response_bytes": len(response),
                        "response_prefix_hex": bytes(response[:64]).hex(),
                        "response_prefix_text": bytes(response[:128]).decode("ascii", errors="backslashreplace"),
                        "response_starts_http1": bytes(response).startswith(b"HTTP/1."),
                        "response_frame_types": response_frame_types(bytes(response)),
                        "peer_closed": peer_closed, "transport_error": transport_error,
                        "target_exit_code_before_cleanup": proc.poll(),
                        "target_alive_after_input": proc.poll() is None})
        finally:
            row["target_exit_code_after_cleanup"] = terminate(proc)
        log.seek(max(0, log.tell() - 2048))
        row["target_log_tail"] = log.read().decode("utf-8", errors="replace")
    return row


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("queue", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    parser.add_argument("--port", type=int, default=20240)
    parser.add_argument("--response-timeout", type=float, default=0.1)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    files = sorted(path for path in args.queue.iterdir() if path.is_file() and not path.name.startswith("."))
    if args.limit is not None:
        files = files[:args.limit]
    rows = [replay(path, args.port, args.response_timeout) for path in files]
    counts = Counter(str(row.get("transport_error") or "ok") for row in rows)
    summary = {
        "queue": str(args.queue), "samples_total": len(files),
        "samples_with_valid_preface": sum(bool(row["preface_valid"]) for row in rows),
        "samples_with_malformed_tail": sum(int(row["malformed_tail_bytes"]) > 0 for row in rows),
        "target_started": sum(bool(row.get("target_started")) for row in rows),
        "target_alive_after_input": sum(bool(row.get("target_alive_after_input")) for row in rows),
        "response_frames": sum(len(row.get("response_frame_types", [])) for row in rows),
        "transport_results": dict(counts), "records": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "records"}, indent=2))


if __name__ == "__main__":
    main()
