#!/usr/bin/env python3
"""Repeat a real Kafka API flow against fresh Redpanda broker processes."""

from __future__ import annotations

import hashlib
import json
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

from prepare_seeds import api_versions, fetch, metadata, produce

HOST = "127.0.0.1"
PORT = 9092
STARTER = os.environ.get("REDPANDA_STARTER", "/home/redpanda/benchmark/start-redpanda.sh")


def read_exact(sock: socket.socket, size: int) -> bytes:
    result = bytearray()
    while len(result) < size:
        part = sock.recv(size - len(result))
        if not part:
            raise ConnectionError(f"broker closed while reading {size} bytes")
        result.extend(part)
    return bytes(result)


def read_frame(sock: socket.socket) -> bytes:
    prefix = read_exact(sock, 4)
    size = int.from_bytes(prefix, "big")
    if size < 4 or size > 16 * 1024 * 1024:
        raise ValueError(f"invalid Kafka response frame length {size}")
    return prefix + read_exact(sock, size)


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


def stop(proc: subprocess.Popen[bytes]) -> int:
    if proc.poll() is None:
        proc.send_signal(signal.SIGTERM)
        try:
            return proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            proc.kill()
    return proc.wait(timeout=5)


def raw_round(index: int, outdir: Path) -> dict[str, object]:
    log_path = outdir / f"redpanda-{index:02d}.log"
    transcript: list[dict[str, object]] = []
    with log_path.open("wb") as log:
        proc = subprocess.Popen(["/bin/bash", STARTER], stdout=log, stderr=subprocess.STDOUT)
        try:
            wait_ready(proc, log_path)
            with socket.create_connection((HOST, PORT), timeout=5) as sock:
                sock.settimeout(15)
                requests = [
                    (18, api_versions(1)),
                    (3, metadata(2)),
                    (0, produce(3, f"raw-redpanda-{index}".encode())),
                    (1, fetch(4)),
                ]
                for api_key, request in requests:
                    sock.sendall(request)
                    reply = read_frame(sock)
                    correlation_id = int.from_bytes(reply[4:8], "big")
                    if correlation_id != len(transcript) + 1:
                        raise AssertionError(f"API {api_key} correlation id mismatch: {correlation_id}")
                    transcript.append({
                        "api_key": api_key,
                        "correlation_id": correlation_id,
                        "response_bytes": len(reply),
                        "response_sha256": hashlib.sha256(reply).hexdigest(),
                    })
            topic = f"redpanda-smoke-{index}"
            broker = f"{HOST}:{PORT}"
            create = subprocess.run(
                ["/usr/bin/rpk", "topic", "create", topic, "-p", "1", "-r", "1", "-X", f"brokers={broker}"],
                capture_output=True, text=True, timeout=30,
            )
            if create.returncode:
                raise RuntimeError(f"rpk topic create failed: {create.stderr[-1000:]}")
            marker = f"rpk-redpanda-smoke-{index}"
            write = subprocess.run(
                ["/usr/bin/rpk", "topic", "produce", topic, "-X", f"brokers={broker}"],
                input=marker + "\n", capture_output=True, text=True, timeout=30,
            )
            if write.returncode:
                raise RuntimeError(f"rpk produce failed: {write.stderr[-1000:]}")
            read = subprocess.run(
                ["/usr/bin/rpk", "topic", "consume", topic, "-n", "1", "-o", "start", "-X", f"brokers={broker}"],
                capture_output=True, text=True, timeout=30,
            )
            if read.returncode or marker not in read.stdout:
                raise RuntimeError(f"rpk consume did not return marker: {read.stderr[-1000:]} {read.stdout[-1000:]}")
            client_flow = {"topic": topic, "marker": marker, "produce_ok": True, "consume_ok": True}
        finally:
            exit_code = stop(proc)
        if exit_code not in (0, 143, -signal.SIGTERM):
            raise RuntimeError(f"Redpanda shutdown had unexpected status {exit_code}; see {log_path}")
        try:
            with socket.create_connection((HOST, PORT), timeout=0.2):
                raise AssertionError("Kafka listener remained open after broker termination")
        except OSError:
            pass
    return {"round": index, "transcript": transcript, "rpk_flow": client_flow, "stop_exit_code": exit_code}


def main() -> int:
    if len(sys.argv) not in (2, 3):
        print("usage: redpanda_smoke.py OUTDIR [repetitions]", file=sys.stderr)
        return 2
    outdir = Path(sys.argv[1])
    repetitions = int(sys.argv[2]) if len(sys.argv) == 3 else 5
    if repetitions < 1 or repetitions > 30:
        raise ValueError("repetitions must be in [1, 30]")
    outdir.mkdir(parents=True, exist_ok=True)
    if any(outdir.iterdir()):
        raise RuntimeError(f"output directory must be empty: {outdir}")
    rounds = [raw_round(index, outdir) for index in range(1, repetitions + 1)]
    normalized = [
        [(entry["api_key"], entry["correlation_id"]) for entry in row["transcript"]]
        for row in rounds
    ]
    stable = all(value == normalized[0] for value in normalized)
    result = {
        "target": "Redpanda v26.2.6 official image",
        "endpoint": f"tcp://{HOST}:{PORT}",
        "protocol_sequence": ["ApiVersions", "Metadata", "Produce", "Fetch"],
        "repetitions": repetitions,
        "normalized_api_sequence_stable": stable,
        "rpk_produce_consume_passed_all_rounds": all(row["rpk_flow"]["consume_ok"] for row in rounds),
        "rounds": rounds,
    }
    (outdir / "protocol-smoke.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if not stable or not result["rpk_produce_consume_passed_all_rounds"]:
        raise AssertionError("protocol smoke was not stable")
    print(f"PASS: {repetitions} fresh-broker Kafka protocol and rpk produce/consume rounds")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, TimeoutError, ValueError, AssertionError, ConnectionError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
