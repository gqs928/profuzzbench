#!/usr/bin/env python3
"""Replay AFLNet queue entries through gcov-enabled INN nnrpd."""
from pathlib import Path
import json
import os
import signal
import socket
import subprocess
import sys
import tarfile
import time

HOST = "127.0.0.1"
PORT = 1119


def connect(proc, timeout=15):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(f"nnrpd exited before readiness: {proc.returncode}")
        try:
            sock = socket.create_connection((HOST, PORT), timeout=1)
            sock.settimeout(0.4)
            greeting = sock.recv(4096)
            return sock, greeting
        except OSError:
            time.sleep(0.1)
    raise TimeoutError("gcov nnrpd did not accept a TCP connection")


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: coverage_replay.py QUEUE_DIR OUTPUT_DIR")
    queue, out = map(Path, sys.argv[1:])
    files = sorted(p for p in queue.iterdir() if p.is_file() and not p.name.startswith("."))
    out.mkdir(parents=True, exist_ok=True)
    log = (out / "nnrpd.server.log").open("wb")
    proc = subprocess.Popen(
        ["/opt/inn-gcov/bin/nnrpd", "-D", "-f", "-4", HOST, "-p", str(PORT), "-n"],
        stdout=log, stderr=subprocess.STDOUT, start_new_session=True,
    )
    results = []
    try:
        for path in files:
            data = path.read_bytes()
            entry = {"sample": path.name, "bytes": len(data), "connected": False,
                     "response_bytes": 0, "timed_out": False, "error": None}
            try:
                sock, greeting = connect(proc)
                entry["connected"] = True
                entry["response_bytes"] = len(greeting)
                if data:
                    sock.sendall(data)
                quiet_deadline = time.monotonic() + 1.0
                hard_deadline = time.monotonic() + 5.0
                while time.monotonic() < hard_deadline:
                    try:
                        response = sock.recv(65536)
                        if not response:
                            break
                        entry["response_bytes"] += len(response)
                        quiet_deadline = time.monotonic() + 0.5
                    except socket.timeout:
                        if time.monotonic() >= quiet_deadline:
                            break
                        continue
                if time.monotonic() >= hard_deadline:
                    entry["timed_out"] = True
                sock.close()
            except Exception as exc:  # preserve all sample failures in the report
                entry["error"] = f"{type(exc).__name__}: {exc}"
            results.append(entry)
    finally:
        if proc.poll() is None:
            os.killpg(proc.pid, signal.SIGTERM)
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait(timeout=5)
        log.close()

    report = {
        "target": "INN 2.7.4 nnrpd gcov build",
        "queue_samples": len(files),
        "connected": sum(item["connected"] for item in results),
        "errors": sum(item["error"] is not None for item in results),
        "timeouts": sum(item["timed_out"] for item in results),
        "samples": results,
    }
    (out / "replay.json").write_text(json.dumps(report, indent=2) + "\n")
    gcda_files = list(Path("/tmp/inn-gcov").rglob("*.gcda"))
    with tarfile.open(out / "gcov-data.tar.gz", "w:gz") as archive:
        for path in gcda_files:
            archive.add(path, arcname=path.relative_to("/tmp/inn-gcov"))
    cov = subprocess.run(
        ["gcovr", "-r", "/tmp/inn-gcov", "/tmp/inn-gcov/nnrpd",
         "-o", str(out / "coverage.txt"), "--print-summary"],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    (out / "gcovr.log").write_text(cov.stdout)
    print(json.dumps({k: v for k, v in report.items() if k != "samples"}, indent=2))
    if cov.returncode:
        raise SystemExit(f"gcovr failed with exit {cov.returncode}; see {out / 'gcovr.log'}")


if __name__ == "__main__":
    main()
