#!/usr/bin/env python3
"""Replay each AFLNet queue item through the coverage-build XMPP listener."""
from pathlib import Path
import json
import os
import signal
import socket
import subprocess
import sys
import time

HOST, PORT = "127.0.0.1", 5222


def start(index: int, log_path: Path) -> subprocess.Popen:
    log = log_path.open("wb")
    proc = subprocess.Popen(["/opt/benchmark/run.sh", "cover"], cwd="/tmp",
                            stdout=log, stderr=subprocess.STDOUT,
                            start_new_session=True, env=dict(os.environ))
    proc._benchmark_log = log
    return proc


def connect(proc: subprocess.Popen, timeout: float = 45.0) -> socket.socket:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(f"ejabberd exited before readiness ({proc.returncode})")
        try:
            sock = socket.create_connection((HOST, PORT), timeout=1.0)
            sock.settimeout(0.3)
            return sock
        except OSError:
            time.sleep(0.1)
    raise TimeoutError("coverage ejabberd did not listen on loopback TCP/5222")


def stop(proc: subprocess.Popen) -> None:
    if proc.poll() is None:
        os.killpg(proc.pid, signal.SIGTERM)
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait(timeout=5)
    proc._benchmark_log.close()


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: coverage_replay.py QUEUE_DIR OUTPUT_DIR")
    queue, out = map(Path, sys.argv[1:])
    files = sorted(path for path in queue.iterdir()
                   if path.is_file() and not path.name.startswith("."))
    out.mkdir(parents=True, exist_ok=True)
    entries = []
    for index, path in enumerate(files):
        item = {"sample": path.name, "bytes": path.stat().st_size,
                "connected": False, "response_bytes": 0,
                "payload_sent": False, "peer_reset_during_read": False,
                "error": None}
        proc = start(index, out / f"server-{index:04d}.log")
        try:
            with connect(proc) as sock:
                item["connected"] = True
                data = path.read_bytes()
                if data:
                    sock.sendall(data)
                    item["payload_sent"] = True
                    try:
                        sock.shutdown(socket.SHUT_WR)
                    except OSError:
                        pass
                deadline = time.monotonic() + 1.5
                while time.monotonic() < deadline:
                    try:
                        chunk = sock.recv(65536)
                    except socket.timeout:
                        break
                    except ConnectionResetError:
                        item["peer_reset_during_read"] = True
                        break
                    if not chunk:
                        break
                    item["response_bytes"] += len(chunk)
        except Exception as exc:
            item["error"] = f"{type(exc).__name__}: {exc}"
        finally:
            stop(proc)
        entries.append(item)
    report = {
        "target": "ejabberd 26.09 XMPP listener",
        "feedback_backend": "AFLNet XMPP response-state feedback; no application source-line coverage",
        "queue_samples": len(files),
        "connected": sum(item["connected"] for item in entries),
        "payloads_sent": sum(item["payload_sent"] for item in entries),
        "peer_resets_during_read": sum(item["peer_reset_during_read"] for item in entries),
        "errors": sum(item["error"] is not None for item in entries),
        "samples": entries,
    }
    (out / "replay.json").write_text(json.dumps(report, indent=2) + "\n")
    (out / "coverage.txt").write_text(
        "Application source coverage was not collected. AFLNet response-state feedback was used.\n"
        f"Queue samples: {report['queue_samples']}\n"
        f"Connected: {report['connected']}\n"
        f"Payloads sent: {report['payloads_sent']}\n"
        f"Peer resets while reading malformed/closing input: {report['peer_resets_during_read']}\n"
        f"Replay errors: {report['errors']}\n")
    print(json.dumps({key: value for key, value in report.items()
                      if key != "samples"}, indent=2))
    if report["errors"]:
        raise SystemExit("one or more queue replays failed; see replay.json")


if __name__ == "__main__":
    main()
