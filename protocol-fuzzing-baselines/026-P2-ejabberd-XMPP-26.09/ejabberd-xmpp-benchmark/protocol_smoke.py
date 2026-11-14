#!/usr/bin/env python3
"""Compare the XMPP stream-features and STARTTLS path across builds."""
from __future__ import annotations

from pathlib import Path
import json
import os
import re
import signal
import socket
import ssl
import subprocess
import sys
import time

HOST, PORT = "127.0.0.1", 5222
OPEN = ("<stream:stream to='localhost' xmlns='jabber:client' "
        "xmlns:stream='http://etherx.jabber.org/streams' version='1.0'>\n").encode()
STARTTLS = b"<starttls xmlns='urn:ietf:params:xml:ns:xmpp-tls'/>\n"
NAME = re.compile(rb"<(?:(?:[A-Za-z_][\w.-]*):)?([A-Za-z_][\w.-]*)\b")


def start(mode: str, log_path: Path) -> subprocess.Popen:
    log = log_path.open("wb")
    proc = subprocess.Popen(["/opt/benchmark/run.sh", mode], cwd="/tmp",
                            stdout=log, stderr=subprocess.STDOUT,
                            start_new_session=True, env=dict(os.environ))
    proc._benchmark_log = log
    return proc


def connect(proc: subprocess.Popen, timeout: float = 45.0) -> socket.socket:
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


def read_until(sock: socket.socket, marker: bytes, timeout: float = 8.0) -> bytes:
    data = bytearray()
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline and marker not in data:
        try:
            chunk = sock.recv(65536)
        except socket.timeout:
            continue
        if not chunk:
            break
        data.extend(chunk)
    if marker not in data:
        raise RuntimeError(f"server response missing {marker!r}: {bytes(data)[:700]!r}")
    return bytes(data)


def tags(data: bytes) -> list[str]:
    return [match.decode("ascii", "replace").lower() for match in NAME.findall(data)]


def run_variant(mode: str, out: Path) -> dict:
    proc = start(mode, out / f"{mode}.server.log")
    try:
        with connect(proc) as sock:
            sock.sendall(OPEN)
            plain = read_until(sock, b"</stream:features>")
            plain_tags = tags(plain)
            if b"starttls" not in plain.lower():
                raise RuntimeError(f"{mode}: initial stream features omit STARTTLS")
            sock.sendall(STARTTLS)
            proceed = read_until(sock, b">")
            if b"proceed" not in proceed.lower():
                raise RuntimeError(f"{mode}: STARTTLS did not return proceed: {proceed!r}")
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            with context.wrap_socket(sock, server_hostname="localhost") as tls:
                tls.sendall(OPEN)
                secure = read_until(tls, b"</stream:features>")
                secure_tags = tags(secure)
        if "features" not in plain_tags or "features" not in secure_tags:
            raise RuntimeError(f"{mode}: stream features stanza not observed")
        return {"plain_feature_tags": plain_tags,
                "starttls_reply": proceed.decode("utf-8", "replace"),
                "tls_feature_tags": secure_tags}
    finally:
        if proc.poll() is None:
            os.killpg(proc.pid, signal.SIGTERM)
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait(timeout=5)
        proc._benchmark_log.close()


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: protocol_smoke.py OUTPUT_DIR")
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    results = {mode: run_variant(mode, out) for mode in ("reference", "afl", "cover")}
    baseline = results["reference"]
    for mode, result in results.items():
        if result["plain_feature_tags"] != baseline["plain_feature_tags"]:
            raise SystemExit(f"{mode}: plaintext XMPP feature path differs from reference")
        if result["tls_feature_tags"] != baseline["tls_feature_tags"]:
            raise SystemExit(f"{mode}: TLS XMPP feature path differs from reference")
    (out / "summary.json").write_text(json.dumps(results, indent=2) + "\n")
    print(json.dumps({"variants": list(results), "port": PORT,
                      "starttls": "passed", "differential_paths": "matched"}, indent=2))
    print("PASS: ejabberd reference/AFL/coverage variants match through XMPP STARTTLS.")


if __name__ == "__main__":
    main()
