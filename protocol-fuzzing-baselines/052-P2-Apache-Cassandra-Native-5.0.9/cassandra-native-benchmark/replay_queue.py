#!/usr/bin/env python3
"""Replay Cassandra raw and AFLNet KL-message queues in fresh node processes."""
from __future__ import annotations

import json
import os
import socket
import struct
import subprocess
import sys
from pathlib import Path

HOST = "127.0.0.1"
PORT = 9042
STARTER = os.environ.get("CASSANDRA_STARTER", "/opt/benchmark/start-cassandra.sh")
RESETTER = os.environ.get("CASSANDRA_RESETTER", "/opt/benchmark/reset-cassandra.sh")
STOPPER = os.environ.get("CASSANDRA_STOPPER", "/opt/benchmark/stop-cassandra.sh")
MAX_FRAME = 16 * 1024 * 1024


def frames_from_raw(data: bytes) -> list[bytes]:
    frames: list[bytes] = []
    offset = 0
    while offset < len(data):
        remaining = len(data) - offset
        if remaining < 9:
            frames.append(data[offset:])
            break
        size = struct.unpack_from(">I", data, offset + 5)[0]
        if size > MAX_FRAME or size > remaining - 9:
            frames.append(data[offset:])
            break
        frame_size = 9 + size
        frames.append(data[offset:offset + frame_size])
        offset += frame_size
    return frames


def frames_from_kl(data: bytes) -> list[bytes]:
    frames: list[bytes] = []
    offset = 0
    while offset < len(data):
        if len(data) - offset < 4:
            raise ValueError("truncated AFLNet KL message length")
        size = struct.unpack_from("<I", data, offset)[0]
        offset += 4
        if not size or size > MAX_FRAME or size > len(data) - offset:
            raise ValueError(f"invalid AFLNet KL frame length {size}")
        frames.append(data[offset:offset + size])
        offset += size
    return frames


def read_exact(sock: socket.socket, count: int) -> bytes:
    out = bytearray()
    while len(out) < count:
        part = sock.recv(count - len(out))
        if not part:
            raise ConnectionError(f"peer closed with {count - len(out)} bytes outstanding")
        out.extend(part)
    return bytes(out)


def read_frame(sock: socket.socket) -> bytes:
    header = read_exact(sock, 9)
    size = struct.unpack_from(">I", header, 5)[0]
    if size > MAX_FRAME:
        raise ValueError(f"invalid Cassandra response length {size}")
    return header + read_exact(sock, size)


def run_hook(path: str, log_path: Path, timeout: int) -> int:
    with log_path.open("ab") as log:
        try:
            return subprocess.run(["/bin/bash", path], stdout=log,
                                  stderr=subprocess.STDOUT, timeout=timeout,
                                  check=False).returncode
        except subprocess.TimeoutExpired:
            return 124


def replay_one(path: Path, mode: str, outdir: Path, index: int) -> dict[str, object]:
    raw = path.read_bytes()
    messages = frames_from_raw(raw) if mode == "raw" else frames_from_kl(raw)
    log_path = outdir / f"{index:05d}-{mode}-{path.name}.log"
    result: dict[str, object] = {"sample": path.name, "mode": mode,
                                "input_bytes": len(raw), "messages": len(messages),
                                "sent": 0, "responses": 0, "response_bytes": 0,
                                "ready": False, "events": []}
    with log_path.open("wb") as log:
        try:
            reset_exit = subprocess.run(["/bin/bash", RESETTER], stdout=log,
                                        stderr=subprocess.STDOUT, timeout=120,
                                        check=False).returncode
            result["reset_exit_code"] = reset_exit
            if reset_exit != 0:
                result["events"].append({"reset_error": f"reset hook exited {reset_exit}"})
                result["log"] = log_path.name
                return result
            result["ready"] = True
            with socket.create_connection((HOST, PORT), timeout=10) as sock:
                sock.settimeout(15)
                for message_index, message in enumerate(messages, start=1):
                    try:
                        sock.sendall(message)
                        result["sent"] = int(result["sent"]) + 1
                    except OSError as exc:
                        result["events"].append({"message": message_index,
                                                 "send_error": repr(exc)})
                        break
                    try:
                        response = read_frame(sock)
                    except (OSError, ValueError) as exc:
                        result["events"].append({"message": message_index,
                                                 "receive_error": repr(exc)})
                        break
                    result["responses"] = int(result["responses"]) + 1
                    result["response_bytes"] = int(result["response_bytes"]) + len(response)
        except (OSError, subprocess.TimeoutExpired, TimeoutError, ValueError) as exc:
            result["events"].append({"session_error": repr(exc)})
    result["log"] = log_path.name
    return result


def main() -> int:
    if len(sys.argv) not in (3, 4):
        print("usage: replay_queue.py CAMPAIGN_DIR OUTDIR [MAX_PER_DIRECTORY]", file=sys.stderr)
        return 2
    campaign, outdir = Path(sys.argv[1]), Path(sys.argv[2])
    maximum = int(sys.argv[3]) if len(sys.argv) == 4 else 100
    if not 1 <= maximum <= 5000:
        raise ValueError("MAX_PER_DIRECTORY must be in [1, 5000]")
    outdir.mkdir(parents=True, exist_ok=True)
    if any(outdir.iterdir()):
        raise RuntimeError(f"output directory must be empty: {outdir}")
    os.environ["CASSANDRA_LIFECYCLE_LOG"] = str(outdir / "cassandra-lifecycle.tsv")
    os.environ["CASSANDRA_LOG_FILE"] = str(outdir / "cassandra-node.log")
    os.environ["CASSANDRA_EXPECTED_VERSION"] = "5.0.9"
    rows: list[dict[str, object]] = []
    index = 0
    stop_exit = 0
    start_exit = run_hook(STARTER, outdir / "target-start.log", 360)
    if start_exit != 0:
        raise RuntimeError(f"Cassandra start hook exited {start_exit}")
    try:
        for name, mode in (("queue", "raw"), ("replayable-queue", "kl"),
                           ("replayable-new-ipsm-paths", "kl")):
            source = campaign / name
            samples = sorted(p for p in source.iterdir()
                             if p.is_file() and p.name.startswith("id:")) if source.is_dir() else []
            for sample in samples[:maximum]:
                index += 1
                rows.append(replay_one(sample, mode, outdir, index))
    finally:
        stop_exit = run_hook(STOPPER, outdir / "target-stop.log", 90)
    summary = {"target": "Apache Cassandra 5.0.9", "protocol": "Cassandra Native Protocol v4",
               "reset": "one isolated Cassandra process; reset-cassandra.sh drops all user keyspaces before each sample, matching the formal fuzz hook",
               "directories": ["queue (raw TCP stream)", "replayable-queue (4-byte LE lengths)",
                               "replayable-new-ipsm-paths (4-byte LE lengths)"],
               "max_per_directory": maximum, "samples": len(rows),
               "ready_samples": sum(bool(row["ready"]) for row in rows),
               "responses": sum(int(row["responses"]) for row in rows),
               "samples_with_events": sum(bool(row["events"]) for row in rows),
               "target_stop_exit_code": stop_exit,
               "rows": rows}
    (outdir / "replay-summary.json").write_text(json.dumps(summary, indent=2) + "\n",
                                                encoding="utf-8")
    print(f"replayed {len(rows)} samples; {summary['ready_samples']} reached readiness; "
          f"{summary['responses']} responses; {summary['samples_with_events']} classified events")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, TimeoutError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
