#!/usr/bin/env python3
"""Replay raw and KL-framed AFLNet DNS/TCP samples in fresh Recursor processes."""
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

HOST = os.environ.get("UNBOUND_HOST", "127.0.0.1")
PORT = int(os.environ.get("UNBOUND_PORT", "5300"))
RESETTER = os.environ.get("UNBOUND_RESETTER", "/opt/benchmark/reset-unbound.sh")
STOPPER = os.environ.get("UNBOUND_STOPPER", "/opt/benchmark/stop-unbound.sh")
PID_FILE = Path(os.environ.get("UNBOUND_PID_FILE", "/tmp/unbound-target.pid"))
MAX_SAMPLE = 16 * 1024 * 1024


def frames_from_kl(data: bytes) -> bytes:
    output = bytearray()
    offset = 0
    while offset < len(data):
        if len(data) - offset < 4:
            raise ValueError("truncated KL-message length")
        size = struct.unpack_from("<I", data, offset)[0]
        offset += 4
        if size < 14 or size > 65537 or size > len(data) - offset:
            raise ValueError(f"invalid KL-message length {size}")
        output.extend(data[offset:offset + size])
        offset += size
    return bytes(output)


def receive_exact(sock: socket.socket, size: int) -> bytes:
    data = bytearray()
    while len(data) < size:
        chunk = sock.recv(size - len(data))
        if not chunk:
            raise EOFError(f"peer closed after {len(data)} of {size} bytes")
        data.extend(chunk)
    return bytes(data)


def read_dns_frames(sock: socket.socket, quiet: float = 0.15,
                    total: float = 1.0) -> tuple[list[dict[str, int]], list[str], bool]:
    frames: list[dict[str, int]] = []
    errors: list[str] = []
    peer_closed = False
    deadline = time.monotonic() + total
    while time.monotonic() < deadline:
        sock.settimeout(max(0.02, min(quiet, deadline - time.monotonic())))
        try:
            prefix = receive_exact(sock, 2)
        except socket.timeout:
            break
        except EOFError:
            peer_closed = True
            break
        length = struct.unpack("!H", prefix)[0]
        if length < 12:
            errors.append(f"invalid_response_length:{length}")
            break
        try:
            body = receive_exact(sock, length)
        except (socket.timeout, EOFError) as exc:
            errors.append(f"incomplete_response:{exc}")
            break
        ident, flags, qd, an, ns, ar = struct.unpack_from("!HHHHHH", body)
        frames.append({"id": ident, "flags": flags, "qr": flags >> 15,
                       "opcode": (flags >> 11) & 15, "aa": (flags >> 10) & 1,
                       "tc": (flags >> 9) & 1, "rcode": flags & 15,
                       "questions": qd, "answers": an, "authority": ns,
                       "additional": ar, "bytes": length})
        deadline = time.monotonic() + quiet
    return frames, errors, peer_closed


def hook(command: str, path: Path, timeout: int) -> int:
    with path.open("ab") as log:
        try:
            return subprocess.run(["/bin/bash", command], stdout=log,
                                  stderr=subprocess.STDOUT, timeout=timeout,
                                  check=False).returncode
        except subprocess.TimeoutExpired:
            return 124


def target_alive() -> bool:
    try:
        pid = int(PID_FILE.read_text().strip())
        os.kill(pid, 0)
        return True
    except (OSError, ValueError):
        return False


def replay_one(path: Path, mode: str, outdir: Path, index: int) -> dict[str, object]:
    raw = path.read_bytes()
    row: dict[str, object] = {"sample": path.name, "mode": mode,
                               "input_bytes": len(raw), "ready": False,
                               "responses": [], "events": []}
    if len(raw) > MAX_SAMPLE:
        row["events"].append({"oversize": True})
        return row
    try:
        payload = raw if mode == "raw" else frames_from_kl(raw)
    except ValueError as exc:
        row["events"].append({"kl_parse_error": str(exc)})
        return row
    log_path = outdir / f"{index:05d}-{mode}-{path.name}.log"
    reset_rc = hook(RESETTER, log_path, 45)
    row["reset_exit_code"] = reset_rc
    if reset_rc != 0:
        row["events"].append({"reset_error": reset_rc})
        return row
    try:
        with socket.create_connection((HOST, PORT), timeout=3.0) as sock:
            row["ready"] = True
            sock.settimeout(1.0)
            sock.sendall(payload)
            row["sent_bytes"] = len(payload)
            responses, errors, peer_closed = read_dns_frames(sock)
            row["responses"] = responses
            if errors:
                row["events"].extend({"response_parse_error": item} for item in errors)
            if peer_closed:
                row["events"].append({"peer_closed": True})
            if not responses and not errors and not peer_closed:
                row["events"].append({"quiet_timeout": True})
    except (OSError, TimeoutError) as exc:
        row["events"].append({"transport_error": str(exc)})
    row["target_alive_after_sample"] = target_alive()
    if not row["target_alive_after_sample"]:
        row["events"].append({"target_process_exited": True})
    row["log"] = log_path.name
    return row


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
        for directory, mode in (("queue", "raw"), ("replayable-queue", "kl"),
                                ("replayable-new-ipsm-paths", "kl")):
            source = campaign / directory
            samples = sorted(p for p in source.iterdir()
                             if p.is_file() and p.name.startswith("id:")) if source.is_dir() else []
            for sample in samples[:maximum]:
                index += 1
                rows.append(replay_one(sample, mode, outdir, index))
    finally:
        stop_rc = hook(STOPPER, outdir / "target-stop.log", 30)
    responses = [r for row in rows for r in row["responses"]]
    event_counts = Counter(str(key) for row in rows for event in row["events"] for key in event)
    summary = {
        "target": "Unbound 1.26.2", "protocol": "DNS/TCP local static-zone query",
        "directories": ["queue (raw DNS/TCP streams)",
                        "replayable-queue (KL little-endian length frames)",
                        "replayable-new-ipsm-paths (KL little-endian length frames)"],
        "samples": len(rows), "ready_samples": sum(bool(row["ready"]) for row in rows),
        "response_count": len(responses),
        "rcode_counts": dict(sorted(Counter(str(r["rcode"]) for r in responses).items())),
        "samples_with_events": sum(bool(row["events"]) for row in rows),
        "target_stop_exit_code": stop_rc, "event_counts": dict(sorted(event_counts.items())),
        "rows": rows,
    }
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
    print(f"replayed {len(rows)} Unbound DNS/TCP samples; {summary['ready_samples']} passed readiness; "
          f"{len(responses)} responses; {summary['samples_with_events']} samples with events")
    return 0 if stop_rc == 0 else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, TimeoutError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
