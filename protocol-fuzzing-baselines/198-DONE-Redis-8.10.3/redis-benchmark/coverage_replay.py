#!/usr/bin/env python3
"""Replay AFLNet's RESP queue on fresh gcov-instrumented Redis servers."""

from __future__ import annotations

import json
import hashlib
import os
import signal
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path


PORT = 6379
MAX_INPUT_BYTES = 1_048_576
MAX_RESPONSE_BYTES = 8_388_608
RESP_TYPES = {
    b":": 210, b"$": 220, b"*": 230, b"%": 231, b"~": 232,
    b"|": 233, b">": 234, b"!": 235, b"=": 236, b"_": 237,
    b"#": 238, b",": 239, b"(": 240, b"+": 203, b"-": 303,
}


def read_resp_line(data: bytes, pos: int) -> tuple[bytes, int] | None:
    end = data.find(b"\r\n", pos)
    if end < 0:
        return None
    return data[pos:end], end + 2


def parse_resp_frame(data: bytes, pos: int = 0, depth: int = 0) -> int | None:
    if pos >= len(data) or depth > 64:
        return None
    marker = data[pos:pos + 1]
    pos += 1
    if marker in (b"+", b"-", b":", b",", b"(", b"#", b"_"):
        line = read_resp_line(data, pos)
        if line is None:
            return None
        return line[1]
    if marker in (b"$", b"!", b"="):
        line = read_resp_line(data, pos)
        if line is None:
            return None
        length_raw, pos = line
        if marker == b"$" and length_raw == b"?":
            while True:
                if pos >= len(data) or data[pos:pos + 1] != b";":
                    return None
                chunk = read_resp_line(data, pos + 1)
                if chunk is None:
                    return None
                chunk_length_raw, pos = chunk
                try:
                    chunk_length = int(chunk_length_raw)
                except ValueError:
                    return None
                if chunk_length == 0:
                    return pos
                if chunk_length < 0 or pos + chunk_length + 2 > len(data):
                    return None
                pos += chunk_length
                if data[pos:pos + 2] != b"\r\n":
                    return None
                pos += 2
        try:
            length = int(length_raw)
        except ValueError:
            return None
        if length == -1 and marker == b"$":
            return pos
        if length < 0 or pos + length + 2 > len(data):
            return None
        if data[pos + length:pos + length + 2] != b"\r\n":
            return None
        return pos + length + 2
    if marker in (b"*", b"%", b"~", b"|", b">"):
        line = read_resp_line(data, pos)
        if line is None:
            return None
        length_raw, pos = line
        if length_raw == b"?":
            while True:
                if data[pos:pos + 1] == b".":
                    end = read_resp_line(data, pos + 1)
                    return end[1] if end is not None and not end[0] else None
                pos = parse_resp_frame(data, pos, depth + 1)
                if pos is None:
                    return None
        try:
            count = int(length_raw)
        except ValueError:
            return None
        if count == -1 and marker == b"*":
            return pos
        if count < 0 or count > 100_000:
            return None
        if marker in (b"%", b"|"):
            count *= 2
        for _ in range(count):
            pos = parse_resp_frame(data, pos, depth + 1)
            if pos is None:
                return None
        return pos
    return None


def response_state(frame: bytes) -> int:
    marker, payload = frame[:1], frame[1:]
    if marker == b"+":
        line = payload.split(b"\r\n", 1)[0]
        return {b"OK": 200, b"PONG": 201, b"QUEUED": 202}.get(line, 203)
    if marker == b"-":
        line = payload.split(b"\r\n", 1)[0]
        code = line.split(b" ", 1)[0]
        return {b"NOAUTH": 300, b"WRONGPASS": 301, b"NOPERM": 302}.get(code, 303)
    return RESP_TYPES.get(marker, 299)


def decode_response_states(data: bytes) -> tuple[list[int], list[str], int]:
    states: list[int] = []
    types: list[str] = []
    pos = 0
    while pos < len(data):
        end = parse_resp_frame(data, pos)
        if end is None or end <= pos:
            break
        frame = data[pos:end]
        states.append(response_state(frame))
        types.append(frame[:1].decode("ascii", errors="replace"))
        pos = end
    return states, types, len(data) - pos


def collect_responses(sock: socket.socket) -> bytes:
    chunks = bytearray()
    quiet_deadline = time.monotonic() + 0.1
    while time.monotonic() < quiet_deadline and len(chunks) < MAX_RESPONSE_BYTES:
        try:
            data = sock.recv(min(65536, MAX_RESPONSE_BYTES - len(chunks)))
        except socket.timeout:
            continue
        except OSError:
            break
        if not data:
            break
        chunks.extend(data)
        quiet_deadline = time.monotonic() + 0.1
    return bytes(chunks)


def queue_files(root: Path) -> list[Path]:
    if root.name == "queue" and root.is_dir():
        candidates = [root]
    elif root.is_dir():
        candidates = sorted(path for path in root.rglob("queue") if path.is_dir())
    else:
        candidates = []
    return sorted(
        {item for directory in candidates for item in directory.iterdir()
         if item.is_file() and item.name.startswith("id:")},
        key=lambda item: item.name,
    )


def stop_server(proc: subprocess.Popen[bytes]) -> int:
    if proc.poll() is None:
        proc.send_signal(signal.SIGTERM)
        try:
            return proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            return proc.wait(timeout=5)
    return proc.returncode or 0


def replay_one(binary: Path, config: str, data: bytes, log_path: Path) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="redis-replay-") as tempdir, log_path.open("wb") as log:
        proc = subprocess.Popen(
            [str(binary), config, "--dir", tempdir], stdout=log,
            stderr=subprocess.STDOUT, start_new_session=True,
        )
        sock: socket.socket | None = None
        status, error = "replayed", ""
        response = b""
        try:
            deadline = time.monotonic() + 10
            while True:
                if proc.poll() is not None:
                    status, error = "server_start_failed", f"Redis exited during startup with {proc.returncode}"
                    break
                try:
                    sock = socket.create_connection(("127.0.0.1", PORT), timeout=0.25)
                    sock.settimeout(0.05)
                    break
                except OSError:
                    if time.monotonic() >= deadline:
                        status, error = "server_start_failed", f"Redis did not listen on {PORT}"
                        break
                    time.sleep(0.025)

            if sock is not None:
                sock.sendall(data)
                response = collect_responses(sock)
                if proc.poll() is not None and proc.returncode not in (0,):
                    status, error = "server_exited", f"Redis exited after input with {proc.returncode}"
        except (OSError, TimeoutError) as exc:
            status, error = "replay_error", str(exc)
        finally:
            if sock is not None:
                sock.close()
            returncode = stop_server(proc)
            log.flush()

    if status == "server_start_failed":
        raise RuntimeError(f"{error}; see {log_path}")
    states, types, response_tail_bytes = decode_response_states(response)
    return {
        "status": status,
        "server_returncode_after_shutdown": returncode,
        "input_bytes": len(data),
        "input_sha256": hashlib.sha256(data).hexdigest(),
        "response_bytes": len(response),
        "response_sha256": hashlib.sha256(response).hexdigest(),
        "response_states": states,
        "response_types": types,
        "response_unparsed_tail_bytes": response_tail_bytes,
        "error": error,
        "log": str(log_path),
    }


def main() -> int:
    if len(sys.argv) != 4:
        print("usage: coverage_replay.py FUZZ_OUTPUT_DIR OUTPUT_DIR QUEUE_LIMIT", file=sys.stderr)
        return 2
    fuzz_dir, output_dir = Path(sys.argv[1]), Path(sys.argv[2])
    limit = int(sys.argv[3])
    binary = Path(os.environ.get("REDIS_GCOV_BIN", ""))
    config = os.environ.get("REDIS_CONFIG", "/workspace/redis.conf")
    if not binary.is_file():
        raise RuntimeError(f"gcov Redis server missing: {binary}")
    if limit < 0:
        raise RuntimeError("QUEUE_LIMIT must be zero (all inputs) or a positive number")
    output_dir.mkdir(parents=True, exist_ok=True)
    if any(output_dir.iterdir()):
        raise RuntimeError(f"coverage replay directory is not empty: {output_dir}")
    all_inputs = queue_files(fuzz_dir)
    if not all_inputs:
        raise RuntimeError(f"no AFLNet queue inputs found below {fuzz_dir}")
    inputs = all_inputs[:limit] if limit else all_inputs
    results: list[dict[str, object]] = []
    for index, path in enumerate(inputs):
        data = path.read_bytes()
        if len(data) > MAX_INPUT_BYTES:
            results.append({"input": path.name, "status": "skipped_oversize", "input_bytes": len(data)})
            continue
        result = replay_one(binary, config, data, output_dir / f"redis-{index:05d}.log")
        result["input"] = path.name
        results.append(result)

    exits = sum(result["status"] == "server_exited" for result in results)
    report = {
        "queue_directory": str(fuzz_dir),
        "queue_inputs_found": len(all_inputs),
        "inputs_replayed_or_skipped": len(results),
        "queue_limit": limit,
        "server_exits_after_input": exits,
        "results": results,
    }
    (output_dir / "replay.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Replayed {len(results)} queue inputs on clean gcov Redis servers; server exits={exits}; evidence={output_dir}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
