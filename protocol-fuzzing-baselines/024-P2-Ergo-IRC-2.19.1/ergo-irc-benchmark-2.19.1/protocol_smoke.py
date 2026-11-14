#!/usr/bin/env python3
"""Compare IRC reply-code paths across three Ergo builds."""
from __future__ import annotations

from pathlib import Path
import json
import os
import re
import socket
import subprocess
import sys
import time

HOST, PORT = "127.0.0.1", 6667
CASES = {
    "registration": b"NICK regtest\r\nUSER regtest 0 * :Benchmark User\r\nQUIT :done\r\n",
    "capability": b"CAP LS 302\r\nCAP END\r\nNICK captest\r\nUSER captest 0 * :Benchmark User\r\nQUIT :done\r\n",
    "channel": b"NICK channelt\r\nUSER channelt 0 * :Benchmark User\r\nJOIN #bench\r\nNAMES #bench\r\nLIST\r\nQUIT :done\r\n",
    "modes-who": b"NICK modetest\r\nUSER modetest 0 * :Benchmark User\r\nJOIN #bench\r\nMODE #bench +nt\r\nWHO #bench\r\nQUIT :done\r\n",
    "unknown-command": b"NICK invalidt\r\nUSER invalidt 0 * :Benchmark User\r\nBOGUS argument\r\nPING :probe\r\nQUIT :done\r\n",
}
NUMERIC = re.compile(rb"(?:^|\s)(\d{3})(?:\s|$)", re.MULTILINE)


def connect(proc: subprocess.Popen, timeout: float = 30.0) -> socket.socket:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(f"Ergo exited during startup ({proc.returncode})")
        try:
            sock = socket.create_connection((HOST, PORT), timeout=1.0)
            sock.settimeout(0.4)
            return sock
        except OSError:
            time.sleep(0.1)
    raise TimeoutError("Ergo did not listen on loopback TCP/6667")


def exchange(sock: socket.socket, data: bytes) -> bytes:
    sock.sendall(data)
    chunks = []
    quiet_deadline = time.monotonic() + 2.0
    hard_deadline = time.monotonic() + 8.0
    while time.monotonic() < hard_deadline:
        try:
            part = sock.recv(65536)
        except socket.timeout:
            if time.monotonic() >= quiet_deadline:
                break
            continue
        except ConnectionResetError:
            break
        if not part:
            break
        chunks.append(part)
        quiet_deadline = time.monotonic() + 0.4
    return b"".join(chunks)


def run_variant(variant: str, out: Path) -> dict:
    prefix = Path(f"/opt/ergo-{variant}")
    data_dir = Path(f"/tmp/ergo-data/smoke-{variant}")
    data_dir.mkdir(parents=True, exist_ok=True)
    log_path = out / f"{variant}.server.log"
    with log_path.open("wb") as log:
        proc = subprocess.Popen(
            [str(prefix / "ergo"), "run", "--conf", "/opt/benchmark/configs/ergo.yaml"],
            cwd=data_dir, stdout=log, stderr=subprocess.STDOUT,
            env=dict(os.environ), start_new_session=True,
        )
        result = {}
        try:
            for name, payload in CASES.items():
                with connect(proc) as sock:
                    transcript = exchange(sock, payload)
                codes = [int(value) for value in NUMERIC.findall(transcript)]
                if not transcript or 1 not in codes:
                    raise RuntimeError(
                        f"{variant}/{name}: missing welcome numeric 001; "
                        f"codes={codes}, reply={transcript[:600]!r}")
                result[name] = {"numeric_replies": codes,
                                "response_bytes": len(transcript)}
        finally:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=5)
    return result


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: protocol_smoke.py OUTPUT_DIR")
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    result = {name: run_variant(name, out) for name in ("reference", "afl", "gcov")}
    (out / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
    if result["reference"] != result["afl"] or result["reference"] != result["gcov"]:
        raise SystemExit("reference/AFL/gcov IRC reply paths differ; see summary.json")
    print(json.dumps({"variants": list(result), "cases": len(CASES),
                      "reply_paths": result["reference"]}, indent=2))
    print("PASS: Ergo 2.19.1 reference/AFL/gcov reply-code paths match.")


if __name__ == "__main__":
    main()
