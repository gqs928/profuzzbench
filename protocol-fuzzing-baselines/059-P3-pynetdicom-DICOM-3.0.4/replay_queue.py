#!/usr/bin/env python3
"""Replay AFLNet raw queue files against a fresh pynetdicom storescp per sample."""
from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import time
from pathlib import Path


def start_server(env: dict[str, str]) -> tuple[bool, str]:
    proc = subprocess.run(["/bin/bash", "/opt/benchmark/start-storescp.sh"],
                          env=env, capture_output=True, text=True, timeout=40)
    return proc.returncode == 0, (proc.stdout + proc.stderr)[-4000:]


def stop_server(env: dict[str, str]) -> None:
    subprocess.run(["/bin/bash", "/opt/benchmark/stop-storescp.sh"],
                   env=env, capture_output=True, text=True, timeout=15)


def collect_responses(sock: socket.socket, quiet: float = 0.4) -> tuple[list[int], int, bool]:
    deadline = time.monotonic() + 3.0
    last_data = time.monotonic()
    data = bytearray()
    timed_out = False
    while time.monotonic() < deadline and len(data) < 4 * 1024 * 1024:
        sock.settimeout(0.1)
        try:
            chunk = sock.recv(65536)
            if not chunk:
                break
            data.extend(chunk)
            last_data = time.monotonic()
        except socket.timeout:
            if data and time.monotonic() - last_data >= quiet:
                timed_out = True
                break
    types: list[int] = []
    offset = 0
    while len(data) - offset >= 6:
        length = int.from_bytes(data[offset + 2:offset + 6], "big")
        if length > len(data) - offset - 6:
            break
        types.append(data[offset])
        offset += 6 + length
    return types, len(data), timed_out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("queue", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--limit", type=int, default=1000)
    parser.add_argument("--port", type=int, default=11112)
    args = parser.parse_args()
    paths = sorted(p for p in args.queue.rglob("*")
                   if p.is_file() and p.name.startswith("id:"))[:args.limit]
    if not paths:
        raise SystemExit(f"no AFLNet queue files found under {args.queue}")
    args.output.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.update({"DICOM_PORT": str(args.port),
                "DICOM_LOG_FILE": str(args.output / "storescp-replay.log"),
                "DICOM_RECEIVE_DIR": "/tmp/pynetdicom-receive"})
    records = []
    for index, path in enumerate(paths):
        entry = {"sample": path.name, "bytes": path.stat().st_size,
                 "server_ready": False, "response_pdus": [], "response_bytes": 0,
                 "timeout_after_response": False, "connection_error": None,
                 "server_alive_after_sample": False}
        ready, detail = start_server(env)
        entry["server_ready"] = ready
        if not ready:
            entry["start_error"] = detail
            records.append(entry)
            stop_server(env)
            continue
        try:
            with socket.create_connection(("127.0.0.1", args.port), timeout=1.0) as sock:
                sock.settimeout(1.0)
                sock.sendall(path.read_bytes())
                try:
                    sock.shutdown(socket.SHUT_WR)
                except OSError:
                    pass
                types, received, timed_out = collect_responses(sock)
                entry["response_pdus"] = types
                entry["response_bytes"] = received
                entry["timeout_after_response"] = timed_out and received > 0
        except (OSError, TimeoutError) as exc:
            entry["connection_error"] = str(exc)
        alive = Path("/tmp/storescp.pid")
        if alive.exists():
            try:
                pid = int(alive.read_text().strip())
                os.kill(pid, 0)
                entry["server_alive_after_sample"] = True
            except (OSError, ValueError):
                entry["server_alive_after_sample"] = False
        stop_server(env)
        records.append(entry)
        if (index + 1) % 100 == 0:
            print(f"replayed {index + 1}/{len(paths)} queue samples", flush=True)
    errors = sum(bool(r.get("connection_error")) for r in records)
    starts = sum(not r["server_ready"] for r in records)
    summary = {
        "queue_path": str(args.queue), "limit": args.limit,
        "samples_selected": len(paths), "samples_replayed": len(records),
        "server_start_failures": starts, "connection_errors": errors,
        "samples_with_response": sum(r["response_bytes"] > 0 for r in records),
        "response_pdu_total": sum(len(r["response_pdus"]) for r in records),
        "response_bytes_total": sum(r["response_bytes"] for r in records),
        "server_alive_after_sample": sum(r["server_alive_after_sample"] for r in records),
        "records_file": "replay-records.json"}
    (args.output / "replay-records.json").write_text(
        json.dumps(records, indent=2) + "\n", encoding="utf-8")
    (args.output / "replay-summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    if starts:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
