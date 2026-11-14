#!/usr/bin/env python3
"""Replay AFLNet queue items one at a time against Go-cover Ergo."""
from pathlib import Path
import json
import os
import signal
import shutil
import socket
import subprocess
import sys
import time

HOST, PORT = "127.0.0.1", 6667
SERVER = "/opt/ergo-gcov/ergo"
CONFIG = "/opt/benchmark/configs/ergo.yaml"
COVER_DIR = "/results/go-cover-data"


def start_server(index: int, log_path: Path) -> subprocess.Popen:
    work = Path(f"/tmp/ergo-data/replay-{index:06d}")
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env["GOCOVERDIR"] = COVER_DIR
    log = log_path.open("ab")
    proc = subprocess.Popen(
        [SERVER, "run", "--conf", CONFIG], cwd=work, env=env,
        stdout=log, stderr=subprocess.STDOUT, start_new_session=True,
    )
    proc._coverage_log = log
    return proc


def connect(proc: subprocess.Popen, timeout: float = 30.0) -> socket.socket:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(f"coverage Ergo exited ({proc.returncode})")
        try:
            sock = socket.create_connection((HOST, PORT), timeout=1.0)
            sock.settimeout(0.3)
            return sock
        except OSError:
            time.sleep(0.1)
    raise TimeoutError("coverage Ergo did not listen on loopback TCP/6667")


def stop_server(proc: subprocess.Popen) -> None:
    if proc.poll() is None:
        os.killpg(proc.pid, signal.SIGINT)
        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait(timeout=5)
    proc._coverage_log.close()


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: coverage_replay.py QUEUE_DIR OUTPUT_DIR")
    queue, out = map(Path, sys.argv[1:])
    out.mkdir(parents=True, exist_ok=True)
    Path(COVER_DIR).mkdir(parents=True, exist_ok=True)
    go_env = dict(os.environ)
    # The container runs as the invoking host UID; HOME may resolve to `/`,
    # which is read-only. Keep Go's tool cache in the writable temp filesystem.
    go_env["GOCACHE"] = "/tmp/go-build-cache"
    files = sorted(path for path in queue.iterdir()
                   if path.is_file() and not path.name.startswith("."))
    results = []
    for index, path in enumerate(files):
        item = {"sample": path.name, "bytes": path.stat().st_size,
                "connected": False, "response_bytes": 0, "error": None}
        proc = start_server(index, out / f"server-{index:04d}.log")
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
    profile = out / "coverage.txt"
    conversion = subprocess.run(
        ["/opt/go/bin/go", "tool", "covdata", "textfmt",
         "-i=" + COVER_DIR, "-o=" + str(profile)],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=go_env,
    )
    (out / "covdata-textfmt.log").write_text(conversion.stdout)
    summary = subprocess.run(
        ["/opt/go/bin/go", "tool", "cover", "-func=" + str(profile)],
        cwd="/opt/ergo-source", text=True, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, env=go_env,
    )
    (out / "go-cover-summary.txt").write_text(summary.stdout)
    report = {
        "target": "Ergo 2.19.1 Go coverage build",
        "coverage_backend": "Go -cover / GOCOVERDIR / go tool covdata",
        "queue_samples": len(files),
        "connected": sum(item["connected"] for item in results),
        "errors": sum(item["error"] is not None for item in results),
        "samples": results,
    }
    (out / "replay.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: value for key, value in report.items()
                      if key != "samples"}, indent=2))
    if conversion.returncode or summary.returncode:
        raise SystemExit("Go coverage conversion failed; see output logs")
    if not profile.exists() or profile.stat().st_size == 0:
        raise SystemExit("Go coverage profile is empty")
    if report["errors"]:
        raise SystemExit("one or more queue replays failed; see replay.json")


if __name__ == "__main__":
    raise SystemExit(main())
