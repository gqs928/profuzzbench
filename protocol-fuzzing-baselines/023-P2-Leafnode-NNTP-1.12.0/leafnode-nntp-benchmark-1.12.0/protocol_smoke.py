#!/usr/bin/env python3
"""Compare NNTP command status paths across Leafnode build variants."""
from __future__ import annotations

from pathlib import Path
import json
import os
import socket
import subprocess
import sys
import time

HOST, PORT = "127.0.0.1", 1119
CASES = {
    "basic": b"CAPABILITIES\r\nMODE READER\r\nQUIT\r\n",
    "metadata": b"HELP\r\nDATE\r\nQUIT\r\n",
    "groups": b"LIST ACTIVE\r\nLIST NEWSGROUPS\r\nQUIT\r\n",
    "articles": b"GROUP comp.test\r\nLISTGROUP comp.test\r\nSTAT 1\r\nQUIT\r\n",
    "extended": b"NEWGROUPS 20260101 000000 GMT\r\nXOVER 1-5\r\nQUIT\r\n",
}


def connect(proc: subprocess.Popen, timeout: float = 15.0) -> socket.socket:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(f"Leafnode listener exited early ({proc.returncode})")
        try:
            sock = socket.create_connection((HOST, PORT), timeout=1.0)
            sock.settimeout(3.0)
            return sock
        except OSError:
            time.sleep(0.1)
    raise TimeoutError("Leafnode did not listen on loopback TCP/1119")


def read_reply(stream) -> tuple[list[int], int]:
    first = stream.readline()
    if not first:
        return [], 0
    codes = [int(first[:3])] if len(first) >= 3 and first[:3].isdigit() else []
    total = len(first)
    if codes and first[3:4] == b"-":
        while True:
            line = stream.readline()
            total += len(line)
            if not line or line in (b".\r\n", b".\n"):
                break
    elif codes and codes[0] in {100, 101, 215, 220, 221, 222, 224, 230, 231, 282}:
        while True:
            line = stream.readline()
            total += len(line)
            if not line or line in (b".\r\n", b".\n"):
                break
    return codes, total


def exchange(sock: socket.socket, payload: bytes) -> tuple[list[int], int]:
    codes, byte_count = [], 0
    stream = sock.makefile("rb")
    try:
        greeting, size = read_reply(stream)
        codes.extend(greeting)
        byte_count += size
        for command in payload.splitlines():
            if not command:
                continue
            sock.sendall(command + b"\r\n")
            reply_codes, size = read_reply(stream)
            codes.extend(reply_codes)
            byte_count += size
            if command.upper() == b"QUIT":
                break
    finally:
        stream.close()
    return codes, byte_count


def run_variant(variant: str, out: Path) -> dict:
    prefix = f"/opt/leafnode-{variant}"
    log_path = out / f"{variant}.server.log"
    with log_path.open("wb") as log:
        env = dict(os.environ, LEAFNODE_PREFIX=prefix)
        proc = subprocess.Popen([f"{prefix}/sbin/leafnode"], stdout=log,
                                stderr=subprocess.STDOUT, env=env)
        rows = {}
        try:
            for name, payload in CASES.items():
                with connect(proc) as sock:
                    codes, response_bytes = exchange(sock, payload)
                if not codes or codes[0] != 200:
                    raise RuntimeError(f"{variant}/{name}: missing NNTP 200 greeting; codes={codes}")
                rows[name] = {"status_codes": codes, "response_bytes": response_bytes}
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)
    return rows


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: protocol_smoke.py OUTPUT_DIR")
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    result = {name: run_variant(name, out) for name in ("reference", "afl", "gcov")}
    if result["reference"] != result["afl"] or result["reference"] != result["gcov"]:
        raise SystemExit("reference/AFL/gcov command status paths differ; see result.json")
    (out / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"variants": list(result), "cases": len(CASES),
                      "status_codes": result["reference"]}, indent=2))
    print("PASS: Leafnode NNTP reference, AFL, and gcov status paths match.")


if __name__ == "__main__":
    main()
