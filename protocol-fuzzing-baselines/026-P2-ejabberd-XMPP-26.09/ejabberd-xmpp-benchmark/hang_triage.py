#!/usr/bin/env python3
"""Replay AFLNet XMPP hang candidates and probe service health independently."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time

HOST, PORT = "127.0.0.1", 5222
OPEN = ("<stream:stream to='localhost' xmlns='jabber:client' "
        "xmlns:stream='http://etherx.jabber.org/streams' version='1.0'>\n").encode()


def start(log_path: Path) -> subprocess.Popen:
    log = log_path.open("wb")
    proc = subprocess.Popen(["/opt/benchmark/run.sh", "afl"], cwd="/tmp",
                            stdout=log, stderr=subprocess.STDOUT,
                            start_new_session=True, env=dict(os.environ))
    proc._benchmark_log = log
    return proc


def connect(proc: subprocess.Popen, timeout: float = 30.0) -> socket.socket:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(f"ejabberd exited during startup ({proc.returncode})")
        try:
            sock = socket.create_connection((HOST, PORT), timeout=1.0)
            sock.settimeout(0.5)
            return sock
        except OSError:
            time.sleep(0.1)
    raise TimeoutError("ejabberd did not listen on loopback TCP/5222")


def recv_features(sock: socket.socket, timeout: float = 6.0) -> bytes:
    data = bytearray()
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            chunk = sock.recv(65536)
        except socket.timeout:
            continue
        if not chunk:
            break
        data.extend(chunk)
        if b"</stream:features>" in data:
            return bytes(data)
    raise TimeoutError(f"XMPP stream features not received: {bytes(data)[:300]!r}")


def stop(proc: subprocess.Popen) -> None:
    if proc.poll() is None:
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            proc.wait(timeout=5)
    proc._benchmark_log.close()


def probe(candidate: Path, out: Path, attempt: int) -> dict:
    proc = start(out / f"server-{attempt:02d}.log")
    result = {"attempt": attempt, "connected": False, "payload_sent": False,
              "response_bytes": 0, "response_timeout": False,
              "peer_reset_during_read": False, "target_alive_after_candidate": False,
              "health_probe_ok": False, "candidate_replay_error": None,
              "health_probe_error": None}
    try:
        try:
            with connect(proc) as sock:
                result["connected"] = True
                sock.sendall(candidate.read_bytes())
                result["payload_sent"] = True
                try:
                    sock.shutdown(socket.SHUT_WR)
                except OSError:
                    pass
                deadline = time.monotonic() + 3.0
                while time.monotonic() < deadline:
                    try:
                        chunk = sock.recv(65536)
                    except socket.timeout:
                        continue
                    except ConnectionResetError:
                        result["peer_reset_during_read"] = True
                        break
                    if not chunk:
                        break
                    result["response_bytes"] += len(chunk)
                else:
                    result["response_timeout"] = True
        except Exception as exc:
            result["candidate_replay_error"] = f"{type(exc).__name__}: {exc}"
        result["target_alive_after_candidate"] = proc.poll() is None
        if result["target_alive_after_candidate"]:
            try:
                with connect(proc) as health:
                    health.sendall(OPEN)
                    response = recv_features(health)
                    result["health_probe_ok"] = b"<stream:features>" in response
            except Exception as exc:
                result["health_probe_error"] = f"{type(exc).__name__}: {exc}"
    finally:
        stop(proc)
    return result


def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit("usage: hang_triage.py CANDIDATE OUTPUT_DIR ATTEMPTS")
    candidate, out = Path(sys.argv[1]), Path(sys.argv[2])
    attempts = int(sys.argv[3])
    if attempts < 1:
        raise SystemExit("ATTEMPTS must be positive")
    out.mkdir(parents=True, exist_ok=True)
    data = candidate.read_bytes()
    results = [probe(candidate, out, attempt) for attempt in range(1, attempts + 1)]
    unavailable = sum(not row["target_alive_after_candidate"] or not row["health_probe_ok"]
                      for row in results)
    report = {
        "candidate": candidate.name,
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "attempts": attempts,
        "service_unavailable_repeats": unavailable,
        "confirmed_service_hang": unavailable >= 2,
        "results": results,
    }
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
