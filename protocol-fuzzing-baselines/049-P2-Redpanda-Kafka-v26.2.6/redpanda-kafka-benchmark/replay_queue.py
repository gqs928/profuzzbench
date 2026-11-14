#!/usr/bin/env python3
"""Replay AFLNet queue files against fresh Redpanda broker processes."""

from __future__ import annotations

import argparse
import json
import os
import signal
import socket
import subprocess
import time
from pathlib import Path

HOST = "127.0.0.1"
PORT = 9092
STARTER = os.environ.get(
    "REDPANDA_STARTER", "/home/redpanda/benchmark/start-redpanda.sh"
)


def wait_ready(proc: subprocess.Popen[bytes], log_path: Path) -> None:
    deadline = time.monotonic() + 45
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(f"Redpanda exited {proc.returncode}; see {log_path}")
        try:
            with socket.create_connection((HOST, PORT), timeout=0.2):
                return
        except OSError:
            time.sleep(0.05)
    raise TimeoutError(f"Redpanda did not open Kafka listener; see {log_path}")


def decode_input(raw: bytes) -> tuple[bytes, str]:
    """Strip AFLNet's replayable queue format: LE packet-size + packet bytes."""
    pieces: list[bytes] = []
    cursor = 0
    while cursor + 4 <= len(raw):
        packet_size = int.from_bytes(raw[cursor:cursor + 4], "little")
        start = cursor + 4
        end = start + packet_size
        if packet_size < 4 or end > len(raw):
            return raw, "raw-network-stream"
        pieces.append(raw[start:end])
        cursor = end
    if pieces and cursor == len(raw):
        return b"".join(pieces), "aflnet-le32-packet-lengths"
    return raw, "raw-network-stream"


def receive_frames(sock: socket.socket, max_frames: int = 128) -> tuple[int, int]:
    frames = 0
    malformed = 0
    sock.settimeout(2.0)
    while frames < max_frames:
        header = bytearray()
        try:
            while len(header) < 4:
                chunk = sock.recv(4 - len(header))
                if not chunk:
                    return frames, malformed
                header.extend(chunk)
        except TimeoutError:
            return frames, malformed
        size = int.from_bytes(header, "big")
        if size < 4 or size > 16 * 1024 * 1024:
            return frames, malformed + 1
        remaining = size
        try:
            while remaining:
                chunk = sock.recv(min(remaining, 65536))
                if not chunk:
                    return frames, malformed + 1
                remaining -= len(chunk)
        except TimeoutError:
            return frames, malformed + 1
        frames += 1
    return frames, malformed


def replay(path: Path, outdir: Path) -> dict[str, object]:
    log_path = outdir / f"{path.name.replace(':', '_')}.log"
    raw_input = path.read_bytes()
    payload, input_format = decode_input(raw_input)
    row: dict[str, object] = {
        "input": path.name,
        "input_bytes": len(raw_input),
        "sent_bytes": len(payload),
        "input_format": input_format,
        "broker_ready": False,
        "connected": False,
        "response_frames": 0,
        "malformed_responses": 0,
        "error": None,
    }
    with log_path.open("wb") as log:
        proc = subprocess.Popen(["/bin/bash", STARTER], stdout=log, stderr=subprocess.STDOUT)
        try:
            wait_ready(proc, log_path)
            row["broker_ready"] = True
            with socket.create_connection((HOST, PORT), timeout=5) as sock:
                row["connected"] = True
                sock.sendall(payload)
                frames, malformed = receive_frames(sock)
                row["response_frames"] = frames
                row["malformed_responses"] = malformed
        except (OSError, RuntimeError, TimeoutError, ValueError) as exc:
            row["error"] = f"{type(exc).__name__}: {exc}"
        finally:
            if proc.poll() is None:
                proc.send_signal(signal.SIGTERM)
                try:
                    proc.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=5)
            row["broker_exit_code"] = proc.returncode
    try:
        with socket.create_connection((HOST, PORT), timeout=0.2):
            row["listener_closed_after_stop"] = False
    except OSError:
        row["listener_closed_after_stop"] = True
    return row


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("queue_dir", type=Path)
    parser.add_argument("outdir", type=Path)
    parser.add_argument("--limit", type=int, default=200)
    args = parser.parse_args()
    if args.limit < 1 or args.limit > 2000:
        parser.error("--limit must be in [1, 2000]")
    args.outdir.mkdir(parents=True, exist_ok=True)
    files = sorted(
        path for path in args.queue_dir.iterdir()
        if path.is_file() and not path.name.startswith(".")
    )[: args.limit]
    rows = [replay(path, args.outdir) for path in files]
    result = {
        "target": "Redpanda v26.2.6 official image",
        "queue_dir": str(args.queue_dir),
        "queue_files_selected": len(files),
        "replayed": len(rows),
        "brokers_ready": sum(bool(row["broker_ready"]) for row in rows),
        "listeners_closed_after_stop": sum(
            bool(row.get("listener_closed_after_stop")) for row in rows
        ),
        "cases": rows,
    }
    output = args.outdir / "queue-replay.json"
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "cases"}, indent=2))
    return 0 if result["replayed"] == result["queue_files_selected"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
