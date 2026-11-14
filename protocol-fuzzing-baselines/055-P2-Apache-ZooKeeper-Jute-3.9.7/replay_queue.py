#!/usr/bin/env python3
"""Replay raw ZooKeeper queue streams and AFLNet KL-message queues."""
from __future__ import annotations

import json
import os
import socket
import struct
import subprocess
import sys
from pathlib import Path

HOST = os.environ.get("ZK_HOST") or socket.gethostbyname(socket.gethostname())
PORT = int(os.environ.get("ZK_PORT", "2181"))
STARTER = os.environ.get("ZK_STARTER", "/opt/benchmark/start-zookeeper.sh")
RESETTER = os.environ.get("ZK_RESETTER", "/opt/benchmark/reset-zookeeper.sh")
STOPPER = os.environ.get("ZK_STOPPER", "/opt/benchmark/stop-zookeeper.sh")
MAX_FRAME = 16 * 1024 * 1024


def frames_from_raw(data: bytes) -> tuple[list[bytes], list[str]]:
    frames: list[bytes] = []
    issues: list[str] = []
    offset = 0
    while offset < len(data):
        remaining = len(data) - offset
        if remaining < 4:
            frames.append(data[offset:])
            issues.append("trailing-bytes-shorter-than-length-prefix")
            break
        size = struct.unpack_from(">I", data, offset)[0]
        if size > MAX_FRAME or size > remaining - 4:
            frames.append(data[offset:])
            issues.append(f"invalid-or-truncated-jute-frame:length={size}:remaining={remaining-4}")
            break
        frame_size = 4 + size
        frames.append(data[offset:offset + frame_size])
        offset += frame_size
    return frames, issues


def frames_from_kl(data: bytes) -> list[bytes]:
    frames: list[bytes] = []
    offset = 0
    while offset < len(data):
        if len(data) - offset < 4:
            raise ValueError("truncated AFLNet KL message length")
        size = struct.unpack_from("<I", data, offset)[0]
        offset += 4
        if not size or size > MAX_FRAME + 4 or size > len(data) - offset:
            raise ValueError(f"invalid AFLNet KL frame length {size}")
        frames.append(data[offset:offset + size])
        offset += size
    return frames


def read_exact(sock: socket.socket, count: int) -> bytes:
    output = bytearray()
    while len(output) < count:
        part = sock.recv(count - len(output))
        if not part:
            raise ConnectionError(f"peer closed with {count - len(output)} bytes outstanding")
        output.extend(part)
    return bytes(output)


def read_packet(sock: socket.socket) -> bytes:
    prefix = read_exact(sock, 4)
    size = struct.unpack(">I", prefix)[0]
    if size > MAX_FRAME:
        raise ValueError(f"response frame exceeds limit: {size}")
    return prefix + read_exact(sock, size)


def classify_packet(packet: bytes, first: bool) -> dict[str, object]:
    body = packet[4:]
    result: dict[str, object] = {"frame_bytes": len(packet), "body_bytes": len(body)}
    if first:
        if len(body) < 21:
            result["classification"] = "short-connect-response"
            return result
        result["classification"] = "connect-response"
        result["protocol_version"] = struct.unpack_from(">i", body)[0]
        result["session_timeout_ms"] = struct.unpack_from(">i", body, 4)[0]
        result["session_id"] = struct.unpack_from(">q", body, 8)[0]
        result["error"] = None
    elif len(body) >= 16:
        xid, zxid, error = struct.unpack_from(">iqi", body)
        result.update({"classification": "reply-header", "xid": xid,
                       "zxid": zxid, "error": error,
                       "payload_bytes": len(body) - 16})
    else:
        result["classification"] = "short-reply-header"
    return result


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
    parse_issues: list[str] = []
    try:
        if mode == "raw":
            messages, parse_issues = frames_from_raw(raw)
        else:
            messages = frames_from_kl(raw)
    except ValueError as exc:
        messages = []
        parse_issues = [str(exc)]

    result: dict[str, object] = {
        "sample": path.name, "mode": mode, "input_bytes": len(raw),
        "messages": len(messages), "sent": 0, "responses": 0,
        "response_bytes": 0, "ready": False, "events": [],
        "parse_issues": parse_issues, "response_states": [],
    }
    log_path = outdir / f"{index:05d}-{mode}-{path.name}.log"
    with log_path.open("wb") as log:
        try:
            reset_code = subprocess.run(["/bin/bash", RESETTER], stdout=log,
                                        stderr=subprocess.STDOUT, timeout=180,
                                        check=False).returncode
            result["reset_exit_code"] = reset_code
            if reset_code != 0:
                result["events"].append({"reset_error": f"reset hook exited {reset_code}"})
                result["log"] = log_path.name
                return result
            result["ready"] = True
            with socket.create_connection((HOST, PORT), timeout=8) as sock:
                sock.settimeout(3.0)
                for frame_index, message in enumerate(messages):
                    try:
                        sock.sendall(message)
                        result["sent"] = int(result["sent"]) + 1
                    except OSError as exc:
                        result["events"].append({"frame": frame_index,
                                                 "send_error": repr(exc)})
                        break
                    try:
                        response = read_packet(sock)
                        result["responses"] = int(result["responses"]) + 1
                        result["response_bytes"] = int(result["response_bytes"]) + len(response)
                        result["response_states"].append(
                            classify_packet(response, first=(frame_index == 0)))
                    except (OSError, ValueError, TimeoutError) as exc:
                        result["events"].append({"frame": frame_index,
                                                 "receive_error": repr(exc)})
                        break
        except (OSError, subprocess.TimeoutExpired, TimeoutError, ValueError) as exc:
            result["events"].append({"session_error": repr(exc)})
    result["log"] = log_path.name
    return result


def main() -> int:
    if len(sys.argv) not in (3, 4):
        print("usage: replay_queue.py CAMPAIGN_DIR OUTDIR [MAX_PER_DIRECTORY]",
              file=sys.stderr)
        return 2
    campaign, outdir = Path(sys.argv[1]), Path(sys.argv[2])
    maximum = int(sys.argv[3]) if len(sys.argv) == 4 else 100
    if not 1 <= maximum <= 5000:
        raise ValueError("MAX_PER_DIRECTORY must be in [1, 5000]")
    outdir.mkdir(parents=True, exist_ok=True)
    if any(outdir.iterdir()):
        raise RuntimeError(f"output directory must be empty: {outdir}")
    os.environ["ZK_LIFECYCLE_LOG"] = str(outdir / "zookeeper-lifecycle.tsv")
    os.environ["ZK_LOG_FILE"] = str(outdir / "zookeeper-node.log")
    os.environ["ZK_HOST"] = HOST
    os.environ["ZK_PORT"] = str(PORT)

    rows: list[dict[str, object]] = []
    index = 0
    start_code = run_hook(STARTER, outdir / "target-start.log", 180)
    if start_code != 0:
        raise RuntimeError(f"ZooKeeper start hook exited {start_code}")
    stop_code = 0
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
        stop_code = run_hook(STOPPER, outdir / "target-stop.log", 60)

    summary = {
        "target": "Apache ZooKeeper 3.9.7",
        "protocol": "ZooKeeper client Jute binary protocol",
        "reset": "restart an isolated server and erase data/dataLog directories before each testcase",
        "directories": ["queue (raw TCP stream)",
                        "replayable-queue (4-byte little-endian lengths)",
                        "replayable-new-ipsm-paths (4-byte little-endian lengths)"],
        "max_per_directory": maximum,
        "samples": len(rows),
        "ready_samples": sum(bool(row["ready"]) for row in rows),
        "responses": sum(int(row["responses"]) for row in rows),
        "samples_with_events": sum(bool(row["events"]) for row in rows),
        "target_stop_exit_code": stop_code,
        "rows": rows,
    }
    (outdir / "replay-summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"replayed {len(rows)} samples; {summary['ready_samples']} reached readiness; "
          f"{summary['responses']} responses; {summary['samples_with_events']} classified events")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, TimeoutError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)

