#!/usr/bin/env python3
"""Exercise valid MongoDB OP_MSG commands on fresh MongoDB Server processes."""

from __future__ import annotations

import hashlib
import json
import os
import signal
import socket
import struct
import subprocess
import sys
import time
from pathlib import Path

from prepare_seeds import parse_messages

HOST = "127.0.0.1"
PORT = 27017
STARTER = os.environ.get(
    "MONGODB_STARTER", "/opt/benchmark/start-mongod.sh"
)


def read_exact(sock: socket.socket, size: int) -> bytes:
    output = bytearray()
    while len(output) < size:
        part = sock.recv(size - len(output))
        if not part:
            raise ConnectionError(f"MongoDB Server closed while reading {size} bytes")
        output.extend(part)
    return bytes(output)


def read_frame(sock: socket.socket) -> bytes:
    header = read_exact(sock, 16)
    length, _, _, opcode = struct.unpack("<iiii", header)
    if length < 21 or length > 16 * 1024 * 1024:
        raise ValueError(f"invalid MongoDB response length {length}")
    if opcode != 2013:
        raise ValueError(f"expected OP_MSG response, got opcode {opcode}")
    return header + read_exact(sock, length - 16)


def bson_ok(frame: bytes) -> int | None:
    if len(frame) < 26 or frame[20] != 0:
        return None
    size = struct.unpack_from("<i", frame, 21)[0]
    start = 21
    end = start + size
    if size < 5 or end > len(frame) or frame[end - 1] != 0:
        return None
    cursor = start + 4
    while cursor < end - 1:
        kind = frame[cursor]
        cursor += 1
        key_end = frame.find(b"\0", cursor, end)
        if key_end < 0:
            return None
        key = frame[cursor:key_end].decode("utf-8", errors="replace")
        cursor = key_end + 1
        value_start = cursor
        if kind == 0x01:
            if cursor + 8 > end:
                return None
            value = struct.unpack_from("<d", frame, cursor)[0]
            cursor += 8
        elif kind == 0x08:
            if cursor + 1 > end:
                return None
            value = frame[cursor] != 0
            cursor += 1
        elif kind == 0x10:
            if cursor + 4 > end:
                return None
            value = struct.unpack_from("<i", frame, cursor)[0]
            cursor += 4
        elif kind == 0x12:
            if cursor + 8 > end:
                return None
            value = struct.unpack_from("<q", frame, cursor)[0]
            cursor += 8
        elif kind in (0x06, 0x0A, 0x7F, 0xFF):
            value = None
        elif kind in (0x03, 0x04):
            if cursor + 4 > end:
                return None
            value_size = struct.unpack_from("<i", frame, cursor)[0]
            if value_size < 5 or cursor + value_size > end:
                return None
            value = None
            cursor += value_size
        elif kind == 0x05:
            if cursor + 5 > end:
                return None
            value_size = struct.unpack_from("<i", frame, cursor)[0]
            if value_size < 0 or cursor + 5 + value_size > end:
                return None
            value = None
            cursor += 5 + value_size
        elif kind == 0x07:
            if cursor + 12 > end:
                return None
            value = None
            cursor += 12
        elif kind in (0x02, 0x0D, 0x0E):
            if cursor + 4 > end:
                return None
            value_size = struct.unpack_from("<i", frame, cursor)[0]
            if value_size < 1 or cursor + 4 + value_size > end:
                return None
            value = None
            cursor += 4 + value_size
        elif kind in (0x09, 0x11):
            if cursor + 8 > end:
                return None
            value = None
            cursor += 8
        elif kind == 0x0B:
            first = frame.find(b"\0", cursor, end)
            second = frame.find(b"\0", first + 1, end) if first >= 0 else -1
            if first < 0 or second < 0:
                return None
            value = None
            cursor = second + 1
        elif kind == 0x0C:
            if cursor + 4 > end:
                return None
            value_size = struct.unpack_from("<i", frame, cursor)[0]
            if value_size < 1 or cursor + 4 + value_size + 12 > end:
                return None
            value = None
            cursor += 4 + value_size + 12
        elif kind == 0x0F:
            if cursor + 4 > end:
                return None
            value_size = struct.unpack_from("<i", frame, cursor)[0]
            if value_size < 4 or cursor + value_size > end:
                return None
            value = None
            cursor += value_size
        elif kind == 0x13:
            if cursor + 16 > end:
                return None
            value = None
            cursor += 16
        else:
            return None
        if key == "ok":
            if isinstance(value, (int, float, bool)):
                return int(value != 0)
            return None
        if cursor <= value_start:
            return None
    return None


def wait_ready(proc: subprocess.Popen[bytes], log_path: Path) -> None:
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(f"MongoDB Server exited {proc.returncode}; see {log_path}")
        try:
            with socket.create_connection((HOST, PORT), timeout=0.2):
                return
        except OSError:
            time.sleep(0.05)
    raise TimeoutError(f"MongoDB Server did not open its listener; see {log_path}")


def stop(proc: subprocess.Popen[bytes]) -> int:
    if proc.poll() is None:
        proc.send_signal(signal.SIGTERM)
        try:
            return proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            proc.kill()
    return proc.wait(timeout=5)


def round_trip(seed_path: Path, outdir: Path, iteration: int) -> dict[str, object]:
    log_path = outdir / f"mongod-{iteration:02d}-{seed_path.stem}.log"
    raw = seed_path.read_bytes()
    messages = parse_messages(raw)
    replies: list[dict[str, object]] = []
    with log_path.open("wb") as log:
        proc = subprocess.Popen(["/bin/bash", STARTER], stdout=log, stderr=subprocess.STDOUT)
        try:
            wait_ready(proc, log_path)
            with socket.create_connection((HOST, PORT), timeout=5) as sock:
                sock.settimeout(20)
                offset = 0
                for request in messages:
                    frame = raw[offset:offset + request["length"]]
                    offset += request["length"]
                    sock.sendall(frame)
                    response = read_frame(sock)
                    _, _, response_to, _ = struct.unpack_from("<iiii", response)
                    state = bson_ok(response)
                    if response_to != request["request_id"]:
                        raise AssertionError(
                            f"responseTo mismatch: {response_to} != {request['request_id']}"
                        )
                    if state != 1:
                        raise AssertionError(
                            f"command reply was not ok for request {request['request_id']}: {state}"
                        )
                    replies.append({
                        "request_id": request["request_id"],
                        "response_to": response_to,
                        "opcode": 2013,
                        "response_bytes": len(response),
                        "ok": state,
                        "sha256": hashlib.sha256(response).hexdigest(),
                    })
        finally:
            exit_code = stop(proc)
        if exit_code not in (0, 143, -signal.SIGTERM):
            raise RuntimeError(f"MongoDB Server shutdown had status {exit_code}; see {log_path}")
    try:
        with socket.create_connection((HOST, PORT), timeout=0.2):
            raise AssertionError("MongoDB listener remained open after mongod termination")
    except OSError:
        pass
    return {"seed": seed_path.name, "iteration": iteration, "responses": replies,
            "stop_exit_code": exit_code, "listener_closed_after_stop": True}


def main() -> int:
    if len(sys.argv) not in (2, 3):
        print("usage: mongodb_smoke.py OUTDIR [repetitions]", file=sys.stderr)
        return 2
    outdir = Path(sys.argv[1])
    repetitions = int(sys.argv[2]) if len(sys.argv) == 3 else 3
    if repetitions < 1 or repetitions > 10:
        raise ValueError("repetitions must be in [1, 10]")
    seeds = sorted(path for path in Path("/opt/benchmark/seeds").glob("*.bin")
                   if path.name.startswith("hello"))
    outdir.mkdir(parents=True, exist_ok=True)
    if any(outdir.iterdir()):
        raise RuntimeError(f"output directory must be empty: {outdir}")
    rows = [round_trip(seed, outdir, i) for i in range(1, repetitions + 1) for seed in seeds]
    result = {
        "target": "MongoDB Server 9.0.8 official linux/amd64 image",
        "protocol": "MongoDB Wire Protocol OP_MSG",
        "seed_count": len(seeds),
        "repetitions": repetitions,
        "successful_command_replies": sum(len(row["responses"]) for row in rows),
        "all_replies_ok": all(all(reply["ok"] == 1 for reply in row["responses"]) for row in rows),
        "all_listeners_closed_after_stop": all(row["listener_closed_after_stop"] for row in rows),
        "rounds": rows,
    }
    (outdir / "protocol-smoke.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if not result["all_replies_ok"] or not result["all_listeners_closed_after_stop"]:
        raise AssertionError("MongoDB Server OP_MSG smoke test was not stable")
    print(f"PASS: {repetitions} fresh-process repetitions over {len(seeds)} MongoDB command flows")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, TimeoutError, ValueError, AssertionError, ConnectionError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
