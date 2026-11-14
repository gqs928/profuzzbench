#!/usr/bin/env python3
"""Replay AFLNet MQTT queue cases on a fresh gcov broker process each."""

from __future__ import annotations

import json
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path


PORT = 1883
CONFIG = os.environ.get("MOSQUITTO_CONFIG", "/workspace/mosquitto.conf")
MAX_INPUT_BYTES = 2_000_000


def queue_files(root: Path) -> list[Path]:
    if root.name == "queue" and root.is_dir():
        candidates = [root]
    elif root.is_dir():
        candidates = sorted(path for path in root.rglob("queue") if path.is_dir())
    else:
        candidates = []
    files = sorted(
        {
            item
            for directory in candidates
            for item in directory.iterdir()
            if item.is_file() and item.name.startswith("id:")
        },
        key=lambda item: item.name,
    )
    if not files:
        raise RuntimeError(f"no AFLNet queue inputs found below {root}")
    return files


def stop_broker(proc: subprocess.Popen[bytes]) -> int:
    if proc.poll() is None:
        proc.send_signal(signal.SIGTERM)
        try:
            return proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            return proc.wait(timeout=5)
    return proc.returncode or 0


def replay_one(binary: Path, data: bytes, log_path: Path) -> dict[str, object]:
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = str(binary.parent.parent / "lib")
    with log_path.open("wb") as log:
        proc = subprocess.Popen(
            [str(binary), "-c", CONFIG],
            stdout=log,
            stderr=subprocess.STDOUT,
            env=env,
            start_new_session=True,
        )
        sock: socket.socket | None = None
        status = "replayed"
        error = ""
        try:
            deadline = time.monotonic() + 10
            while True:
                if proc.poll() is not None:
                    status = "broker_start_failed"
                    error = f"broker exited during startup with {proc.returncode}"
                    break
                try:
                    probe = socket.create_connection(("127.0.0.1", PORT), timeout=0.2)
                    probe.close()
                    break
                except OSError:
                    if time.monotonic() >= deadline:
                        status = "broker_start_failed"
                        error = f"broker did not listen on port {PORT}"
                        break
                    time.sleep(0.025)

            if status == "replayed":
                sock = socket.create_connection(("127.0.0.1", PORT), timeout=2)
                sock.settimeout(0.025)
                sock.sendall(data)
                quiet_deadline = time.monotonic() + 0.15
                while time.monotonic() < quiet_deadline:
                    try:
                        if not sock.recv(65536):
                            break
                    except socket.timeout:
                        continue
                    except OSError:
                        break
                if proc.poll() is not None and proc.returncode not in (0,):
                    status = "broker_exited"
                    error = f"broker exited after input with {proc.returncode}"
        except (OSError, TimeoutError) as exc:
            status = "replay_error"
            error = str(exc)
        finally:
            if sock is not None:
                sock.close()
            returncode = stop_broker(proc)
            log.flush()

    if status == "broker_start_failed":
        raise RuntimeError(f"{error}; see {log_path}")
    return {
        "status": status,
        "broker_returncode_after_shutdown": returncode,
        "input_bytes": len(data),
        "error": error,
        "log": str(log_path),
    }


def main() -> int:
    if len(sys.argv) != 4:
        print("usage: coverage_replay.py FUZZ_OUTPUT_DIR OUTPUT_DIR QUEUE_LIMIT", file=sys.stderr)
        return 2
    fuzz_dir, output_dir = Path(sys.argv[1]), Path(sys.argv[2])
    limit = int(sys.argv[3])
    binary = Path(os.environ.get("MOSQUITTO_GCOV_BIN", ""))
    if not binary.is_file():
        raise RuntimeError(f"gcov broker binary missing: {binary}")
    if limit < 0:
        raise RuntimeError("QUEUE_LIMIT must be zero (all inputs) or a positive number")
    output_dir.mkdir(parents=True, exist_ok=True)
    if any(output_dir.iterdir()):
        raise RuntimeError(f"coverage replay directory is not empty: {output_dir}")

    inputs = queue_files(fuzz_dir)
    if limit:
        inputs = inputs[:limit]
    results: list[dict[str, object]] = []
    for index, path in enumerate(inputs):
        data = path.read_bytes()
        if len(data) > MAX_INPUT_BYTES:
            results.append(
                {"input": path.name, "status": "skipped_oversize", "input_bytes": len(data)}
            )
            continue
        result = replay_one(binary, data, output_dir / f"broker-{index:05d}.log")
        result["input"] = path.name
        results.append(result)

    crashes = sum(result["status"] == "broker_exited" for result in results)
    report = {
        "queue_directory": str(fuzz_dir),
        "queue_inputs_found": len(queue_files(fuzz_dir)),
        "inputs_replayed_or_skipped": len(results),
        "queue_limit": limit,
        "broker_exits_after_input": crashes,
        "results": results,
    }
    (output_dir / "replay.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"Replayed {len(results)} queue inputs on clean gcov brokers; "
        f"broker exits after input={crashes}; evidence={output_dir}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
