#!/usr/bin/env python3
"""Replay raw AFLNet streams and KL-framed BGP message queues."""
from __future__ import annotations

import json
import os
import socket
import struct
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

HOST = os.environ.get("BGP_HOST", "127.0.0.1")
PORT = int(os.environ.get("BGP_PORT", "179"))
RESETTER = os.environ.get("BGP_RESETTER", "/opt/benchmark/reset-bgpd.sh")
STOPPER = os.environ.get("BGP_STOPPER", "/opt/benchmark/stop-bgpd.sh")
PID_FILE = os.environ.get("BGPD_PID_FILE", "/tmp/frr-benchmark-bgpd.pid")
MARKER = b"\xff" * 16
MAX_SAMPLE = 16 * 1024 * 1024
TYPE_NAMES = {1: "OPEN", 2: "UPDATE", 3: "NOTIFICATION", 4: "KEEPALIVE", 5: "ROUTE-REFRESH"}


def frames_from_kl(data: bytes) -> list[bytes]:
    frames: list[bytes] = []
    offset = 0
    while offset < len(data):
        if len(data) - offset < 4:
            raise ValueError("truncated KL-message length")
        size = struct.unpack_from("<I", data, offset)[0]
        offset += 4
        if size < 19 or size > 65535 or size > len(data) - offset:
            raise ValueError(f"invalid KL-message length {size}")
        frames.append(data[offset:offset + size])
        offset += size
    return frames


def classify_messages(data: bytes) -> tuple[list[dict[str, object]], int]:
    messages: list[dict[str, object]] = []
    offset = 0
    malformed = 0
    while len(data) - offset >= 19:
        marker = data[offset:offset + 16]
        length, kind = struct.unpack_from(">HB", data, offset + 16)
        if marker != MARKER or length < 19 or length > 65535:
            malformed += 1
            break
        if len(data) - offset < length:
            malformed += 1
            break
        body = data[offset + 19:offset + length]
        item: dict[str, object] = {"type": TYPE_NAMES.get(kind, f"UNKNOWN_{kind}"),
                                   "type_code": kind, "length": length}
        if kind == 1 and len(body) >= 10:
            item["version"] = body[0]
            item["as"] = struct.unpack_from(">H", body, 1)[0]
            item["hold_time"] = struct.unpack_from(">H", body, 3)[0]
        if kind == 3 and len(body) >= 2:
            item["notification_code"] = body[0]
            item["notification_subcode"] = body[1]
        messages.append(item)
        offset += length
    if offset < len(data) and len(data) - offset < 19:
        malformed += 1
    return messages, malformed


def run_hook(path: str, log_path: Path, timeout: int) -> int:
    with log_path.open("ab") as log:
        try:
            return subprocess.run(["/bin/bash", path], stdout=log,
                                  stderr=subprocess.STDOUT, timeout=timeout,
                                  check=False).returncode
        except subprocess.TimeoutExpired:
            return 124


def target_alive() -> bool:
    try:
        pid = int(Path(PID_FILE).read_text().strip())
        os.kill(pid, 0)
        return True
    except (OSError, ValueError):
        return False


def replay_one(path: Path, mode: str, outdir: Path, index: int) -> dict[str, object]:
    raw = path.read_bytes()
    result: dict[str, object] = {"sample": path.name, "mode": mode,
                                 "input_bytes": len(raw), "responses": [],
                                 "sent_bytes": 0, "ready": False, "events": []}
    if len(raw) > MAX_SAMPLE:
        result["events"].append({"oversize": True})
        return result
    try:
        payload = raw if mode == "raw" else b"".join(frames_from_kl(raw))
    except ValueError as exc:
        result["events"].append({"kl_parse_error": str(exc)})
        return result
    log_path = outdir / f"{index:05d}-{mode}-{path.name}.log"
    with log_path.open("wb") as log:
        reset = run_hook(RESETTER, log_path, 60)
        result["reset_exit_code"] = reset
        if reset != 0:
            result["events"].append({"reset_error": reset})
            return result
        try:
            with socket.create_connection((HOST, PORT), timeout=3.0) as sock:
                result["ready"] = True
                sock.settimeout(2.0)
                sock.sendall(payload)
                result["sent_bytes"] = len(payload)
                buf = bytearray()
                peer_closed = False
                deadline = time.monotonic() + 0.25
                while time.monotonic() < deadline:
                    sock.settimeout(max(0.02, deadline - time.monotonic()))
                    try:
                        chunk = sock.recv(65536)
                    except socket.timeout:
                        break
                    if not chunk:
                        peer_closed = True
                        break
                    buf.extend(chunk)
                    deadline = time.monotonic() + 0.15
                messages, malformed = classify_messages(bytes(buf))
                result["responses"] = messages
                result["response_bytes"] = len(buf)
                result["malformed_response_bytes"] = malformed
                if peer_closed:
                    result["events"].append({"peer_closed": True})
        except (OSError, TimeoutError) as exc:
            result["events"].append({"transport_error": str(exc)})
    result["target_alive_after_sample"] = target_alive()
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
    rows: list[dict[str, object]] = []
    index = 0
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
        stop_code = run_hook(STOPPER, outdir / "target-stop.log", 30)
    responses = [msg for row in rows for msg in row["responses"]]
    event_counts = Counter(str(event_key) for row in rows
                           for event in row["events"] for event_key in event)
    summary = {"target": "FRRouting 10.7.1 bgpd", "protocol": "BGP-4",
               "directories": ["queue (raw TCP streams)",
                               "replayable-queue (KL little-endian length frames)",
                               "replayable-new-ipsm-paths (KL little-endian length frames)"],
               "max_per_directory": maximum, "samples": len(rows),
               "ready_samples": sum(bool(row["ready"]) for row in rows),
               "response_message_count": len(responses),
               "response_type_counts": dict(sorted(Counter(str(m["type"]) for m in responses).items())),
               "samples_with_events": sum(bool(row["events"]) for row in rows),
               "target_stop_exit_code": stop_code, "event_counts": dict(sorted(event_counts.items())),
               "rows": rows}
    (outdir / "replay-summary.json").write_text(json.dumps(summary, indent=2) + "\n",
                                               encoding="utf-8")
    for path in sorted(outdir.rglob("*"), reverse=True):
        try:
            path.chmod(path.stat().st_mode | 0o444 | (0o111 if path.is_dir() else 0))
        except OSError:
            pass
    try:
        outdir.chmod(outdir.stat().st_mode | 0o555)
    except OSError:
        pass
    print(f"replayed {len(rows)} BGP samples; {summary['ready_samples']} reached readiness; "
          f"{len(responses)} response messages; {summary['samples_with_events']} samples with events")
    return 0 if stop_code == 0 else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, TimeoutError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
