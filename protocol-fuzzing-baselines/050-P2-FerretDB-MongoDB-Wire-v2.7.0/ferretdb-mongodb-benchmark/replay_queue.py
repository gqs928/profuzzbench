#!/usr/bin/env python3
"""Replay AFLNet MongoDB queues against a fresh FerretDB process per sample."""

from __future__ import annotations

import json
import os
import signal
import socket
import struct
import subprocess
import sys
import time
from pathlib import Path

from ferretdb_smoke import HOST, PORT, bson_ok, read_exact

STARTER = os.environ.get("FERRETDB_STARTER", "/opt/benchmark/start-ferretdb.sh")
MAX_FRAME = 16 * 1024 * 1024


def frames_from_raw(data: bytes) -> list[bytes]:
    """Split raw MongoDB wire frames; retain any malformed tail as one frame."""
    frames: list[bytes] = []
    offset = 0
    while offset < len(data):
        remaining = len(data) - offset
        if remaining < 16:
            frames.append(data[offset:])
            break
        size = struct.unpack_from("<i", data, offset)[0]
        if size < 16 or size > remaining or size > MAX_FRAME:
            frames.append(data[offset:])
            break
        frames.append(data[offset:offset + size])
        offset += size
    return frames


def frames_from_kl(data: bytes) -> list[bytes]:
    """Decode AFLNet replayable files (u32 little-endian size + message)."""
    frames: list[bytes] = []
    offset = 0
    while offset < len(data):
        if len(data) - offset < 4:
            raise ValueError("truncated AFLNet replayable message length")
        size = struct.unpack_from("<I", data, offset)[0]
        offset += 4
        if not size or size > MAX_FRAME or size > len(data) - offset:
            raise ValueError(f"invalid AFLNet replayable message size {size}")
        frames.append(data[offset:offset + size])
        offset += size
    return frames


def read_frame(sock: socket.socket) -> bytes:
    header = read_exact(sock, 16)
    length, _, _, _ = struct.unpack("<iiii", header)
    if length < 16 or length > MAX_FRAME:
        raise ValueError(f"invalid MongoDB response length {length}")
    return header + read_exact(sock, length - 16)


def wait_ready(proc: subprocess.Popen[bytes], log_path: Path) -> None:
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(f"FerretDB exited {proc.returncode}; see {log_path}")
        try:
            with socket.create_connection((HOST, PORT), timeout=0.2):
                return
        except OSError:
            time.sleep(0.05)
    raise TimeoutError(f"FerretDB did not open MongoDB listener; see {log_path}")


def stop(proc: subprocess.Popen[bytes]) -> int:
    if proc.poll() is None:
        proc.send_signal(signal.SIGTERM)
        try:
            return proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            proc.kill()
    return proc.wait(timeout=5)


def replay_one(path: Path, mode: str, outdir: Path, index: int) -> dict[str, object]:
    raw = path.read_bytes()
    frame_list = frames_from_raw(raw) if mode == "raw" else frames_from_kl(raw)
    log_path = outdir / f"{index:05d}-{mode}-{path.name}.log"
    result: dict[str, object] = {
        "sample": path.name,
        "mode": mode,
        "input_bytes": len(raw),
        "messages": len(frame_list),
        "sent": 0,
        "responses": 0,
        "response_bytes": 0,
        "ok_replies": 0,
        "error_replies": 0,
        "other_replies": 0,
        "events": [],
    }
    with log_path.open("wb") as log:
        proc = subprocess.Popen(["/bin/bash", STARTER], stdout=log, stderr=subprocess.STDOUT)
        try:
            wait_ready(proc, log_path)
            with socket.create_connection((HOST, PORT), timeout=5) as sock:
                sock.settimeout(10)
                for message_index, message in enumerate(frame_list, start=1):
                    try:
                        sock.sendall(message)
                        result["sent"] = int(result["sent"]) + 1
                    except OSError as exc:
                        result["events"].append({"message": message_index, "send_error": repr(exc)})
                        break
                    try:
                        reply = read_frame(sock)
                    except (OSError, ValueError) as exc:
                        result["events"].append({"message": message_index, "receive_error": repr(exc)})
                        break
                    result["responses"] = int(result["responses"]) + 1
                    result["response_bytes"] = int(result["response_bytes"]) + len(reply)
                    state = bson_ok(reply)
                    if state == 1:
                        result["ok_replies"] = int(result["ok_replies"]) + 1
                    elif state == 0:
                        result["error_replies"] = int(result["error_replies"]) + 1
                    else:
                        result["other_replies"] = int(result["other_replies"]) + 1
        except (OSError, RuntimeError, TimeoutError) as exc:
            result["events"].append({"session_error": repr(exc)})
        finally:
            result["stop_exit_code"] = stop(proc)
    result["log"] = log_path.name
    return result


def main() -> int:
    if len(sys.argv) not in (3, 4):
        print("usage: replay_queue.py CAMPAIGN_DIR OUTDIR [MAX_PER_DIRECTORY]", file=sys.stderr)
        return 2
    campaign = Path(sys.argv[1])
    outdir = Path(sys.argv[2])
    maximum = int(sys.argv[3]) if len(sys.argv) == 4 else 300
    if maximum < 1 or maximum > 5000:
        raise ValueError("MAX_PER_DIRECTORY must be in [1, 5000]")
    outdir.mkdir(parents=True, exist_ok=True)
    if any(outdir.iterdir()):
        raise RuntimeError(f"output directory must be empty: {outdir}")

    rows: list[dict[str, object]] = []
    index = 0
    for name, mode in (("queue", "raw"), ("replayable-queue", "kl"),
                       ("replayable-new-ipsm-paths", "kl")):
        source = campaign / name
        samples = sorted(path for path in source.iterdir()
                         if path.is_file() and path.name.startswith("id:")) if source.is_dir() else []
        selected = samples[:maximum]
        for sample in selected:
            index += 1
            rows.append(replay_one(sample, mode, outdir, index))

    summary = {
        "target": "FerretDB v2.7.0",
        "protocol": "MongoDB Wire Protocol OP_MSG",
        "reset": "fresh FerretDB process and DocumentDB drop_database reset per sample",
        "directories": ["queue (raw TCP stream)", "replayable-queue (4-byte LE message lengths)",
                        "replayable-new-ipsm-paths (4-byte LE message lengths)"],
        "max_per_directory": maximum,
        "samples": len(rows),
        "responses": sum(int(row["responses"]) for row in rows),
        "ok_replies": sum(int(row["ok_replies"]) for row in rows),
        "error_replies": sum(int(row["error_replies"]) for row in rows),
        "other_replies": sum(int(row["other_replies"]) for row in rows),
        "samples_with_events": sum(bool(row["events"]) for row in rows),
        "rows": rows,
    }
    (outdir / "replay-summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: replayed {len(rows)} samples; {summary['responses']} responses; "
          f"{summary['samples_with_events']} samples with classified events")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, TimeoutError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
