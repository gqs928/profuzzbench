#!/usr/bin/env python3
"""Replay AFLNet queue samples through the gcov-enabled Leafnode listener."""
from pathlib import Path
import json
import os
import signal
import socket
import subprocess
import sys
import time

HOST, PORT = "127.0.0.1", 1119


def connect(proc: subprocess.Popen, timeout: float = 15.0) -> socket.socket:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(f"gcov listener exited early ({proc.returncode})")
        try:
            sock = socket.create_connection((HOST, PORT), timeout=1.0)
            sock.settimeout(0.4)
            return sock
        except OSError:
            time.sleep(0.1)
    raise TimeoutError("gcov Leafnode listener did not accept TCP/1119")


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: coverage_replay.py QUEUE_DIR OUTPUT_DIR")
    queue, out = map(Path, sys.argv[1:])
    files = sorted(p for p in queue.iterdir() if p.is_file() and not p.name.startswith("."))
    out.mkdir(parents=True, exist_ok=True)
    log = (out / "server.log").open("wb")
    env = dict(os.environ, LEAFNODE_PREFIX="/opt/leafnode-gcov")
    proc = subprocess.Popen(["/opt/leafnode-gcov/sbin/leafnode"], stdout=log,
                            stderr=subprocess.STDOUT, env=env, start_new_session=True)
    entries = []
    try:
        for path in files:
            item = {"sample": path.name, "bytes": path.stat().st_size,
                    "connected": False, "response_bytes": 0,
                    "peer_reset_during_read": False, "error": None}
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
                    sock.shutdown(socket.SHUT_WR)
                    deadline = time.monotonic() + 4.0
                    while time.monotonic() < deadline:
                        try:
                            chunk = sock.recv(65536)
                        except socket.timeout:
                            break
                        except ConnectionResetError:
                            # Leafnode closes connections abruptly for some
                            # malformed NNTP inputs after accepting the sample.
                            # A reset while draining the reply is a target
                            # response, not a replay transport failure.
                            item["peer_reset_during_read"] = True
                            break
                        if not chunk:
                            break
                        item["response_bytes"] += len(chunk)
            except Exception as exc:
                item["error"] = f"{type(exc).__name__}: {exc}"
            entries.append(item)
    finally:
        if proc.poll() is None:
            os.killpg(proc.pid, signal.SIGTERM)
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait(timeout=5)
        log.close()
    report = {"target": "Leafnode 1.12.0 gcov NNTP listener",
              "queue_samples": len(files),
              "connected": sum(x["connected"] for x in entries),
              "peer_resets_during_read": sum(x["peer_reset_during_read"] for x in entries),
              "errors": sum(x["error"] is not None for x in entries),
              "samples": entries}
    (out / "replay.json").write_text(json.dumps(report, indent=2) + "\n")
    cov = subprocess.run(
        ["gcovr", "-r", "/tmp/leafnode-gcov", "/tmp/leafnode-gcov",
         "--print-summary", "-o", str(out / "coverage.txt")],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    (out / "gcovr.log").write_text(cov.stdout)
    print(json.dumps({k: v for k, v in report.items() if k != "samples"}, indent=2))
    if cov.returncode:
        raise SystemExit(f"gcovr exited {cov.returncode}; see {out / 'gcovr.log'}")
    if report["errors"]:
        raise SystemExit("one or more queue samples failed; see replay.json")


if __name__ == "__main__":
    main()
