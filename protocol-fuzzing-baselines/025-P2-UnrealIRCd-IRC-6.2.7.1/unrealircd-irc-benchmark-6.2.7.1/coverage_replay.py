#!/usr/bin/env python3
"""Replay AFLNet queue entries against the gcov-enabled UnrealIRCd."""
from pathlib import Path
import json
import os
import signal
import socket
import subprocess
import sys
import time

HOST, PORT = "127.0.0.1", 6667
SERVER = "/opt/unreal-gcov/bin/unrealircd"
CONFIG = "/opt/unreal-gcov/conf/unrealircd.conf"


def start_server(log_path: Path) -> subprocess.Popen:
    log = log_path.open("ab")
    proc = subprocess.Popen([SERVER, "-F", "-f", CONFIG],
                            cwd="/opt/unreal-gcov", stdout=log,
                            stderr=subprocess.STDOUT, start_new_session=True)
    proc._coverage_log = log
    return proc


def connect(proc: subprocess.Popen, timeout: float = 20.0) -> socket.socket:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(f"gcov UnrealIRCd exited ({proc.returncode})")
        try:
            sock = socket.create_connection((HOST, PORT), timeout=1.0)
            sock.settimeout(0.3)
            return sock
        except OSError:
            time.sleep(0.1)
    raise TimeoutError("gcov UnrealIRCd did not listen on loopback TCP/6667")


def stop_server(proc: subprocess.Popen) -> None:
    if proc.poll() is None:
        os.killpg(proc.pid, signal.SIGTERM)
        try:
            proc.wait(timeout=8)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait(timeout=5)
    proc._coverage_log.close()


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: coverage_replay.py QUEUE_DIR OUTPUT_DIR")
    queue, out = map(Path, sys.argv[1:])
    files = sorted(p for p in queue.iterdir() if p.is_file() and not p.name.startswith("."))
    out.mkdir(parents=True, exist_ok=True)
    results = []
    for index, path in enumerate(files):
        item = {"sample": path.name, "bytes": path.stat().st_size,
                "connected": False, "response_bytes": 0, "error": None}
        proc = start_server(out / f"server-{index:04d}.log")
        try:
            with connect(proc) as sock:
                item["connected"] = True
                try:
                    greeting = sock.recv(4096)
                except socket.timeout:
                    greeting = b""
                item["response_bytes"] += len(greeting)
                data = path.read_bytes()
                if data:
                    sock.sendall(data)
                deadline = time.monotonic() + 2.0
                while time.monotonic() < deadline:
                    try:
                        chunk = sock.recv(65536)
                    except socket.timeout:
                        break
                    except ConnectionResetError:
                        break
                    if not chunk:
                        break
                    item["response_bytes"] += len(chunk)
        except Exception as exc:
            item["error"] = f"{type(exc).__name__}: {exc}"
        finally:
            stop_server(proc)
        results.append(item)
    report = {"target": "UnrealIRCd 6.2.7.1 gcov IRC build",
              "queue_samples": len(files),
              "connected": sum(x["connected"] for x in results),
              "errors": sum(x["error"] is not None for x in results),
              "samples": results}
    (out / "replay.json").write_text(json.dumps(report, indent=2) + "\n")
    cov = subprocess.run(
        ["gcovr", "-r", "/tmp/unreal-gcov", "/tmp/unreal-gcov",
         "--print-summary", "-o", str(out / "coverage.txt")],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    (out / "gcovr.log").write_text(cov.stdout)
    print(json.dumps({k: v for k, v in report.items() if k != "samples"}, indent=2))
    if cov.returncode:
        raise SystemExit(f"gcovr exited {cov.returncode}; see {out / 'gcovr.log'}")
    if report["errors"]:
        raise SystemExit("one or more queue replays failed; see replay.json")


if __name__ == "__main__":
    main()
