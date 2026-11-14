#!/usr/bin/env python3
"""Compare IRC numeric reply paths across UnrealIRCd build variants."""
from __future__ import annotations

from pathlib import Path
import json
import os
import re
import socket
import ssl
import subprocess
import sys
import time

HOST, PORT = "127.0.0.1", 6667
CASES = {
    # Each case separates registration from post-registration commands so the
    # smoke client does not pipeline JOIN/PRIVMSG before it has received 001.
    "registration": (b"NICK regtest\r\nUSER regtest 0 * :Benchmark User\r\n", b""),
    "cap-join": (
        b"CAP LS 302\r\nNICK captest\r\nUSER captest 0 * :Benchmark User\r\nCAP END\r\n",
        b"JOIN #bench\r\n",
    ),
    "message-ping": (
        b"NICK msgtest\r\nUSER msgtest 0 * :Benchmark User\r\n",
        b"JOIN #bench\r\nPRIVMSG #bench :hello\r\nPING :probe\r\n",
    ),
    "modes-who": (
        b"NICK modetest\r\nUSER modetest 0 * :Benchmark User\r\n",
        b"JOIN #bench\r\nMODE #bench +nt\r\nWHO #bench\r\nNAMES #bench\r\n",
    ),
    "unsupported-cap": (
        b"CAP LS 302\r\nCAP REQ :sasl\r\nNICK invalidtest\r\nUSER invalidtest 0 * :Benchmark User\r\nCAP END\r\n",
        b"AWAY :benchmark\r\nPING :probe\r\n",
    ),
}
NUMERIC = re.compile(rb"(?:^|\s)(\d{3})(?:\s|$)", re.MULTILINE)


def connect(proc: subprocess.Popen, timeout: float = 20.0) -> socket.socket:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(f"UnrealIRCd exited during startup ({proc.returncode})")
        try:
            sock = socket.create_connection((HOST, PORT), timeout=1.0)
            sock.settimeout(0.5)
            return sock
        except OSError:
            time.sleep(0.1)
    raise TimeoutError("UnrealIRCd did not listen on loopback TCP/6667")


def connect_tls(proc: subprocess.Popen, timeout: float = 20.0) -> ssl.SSLSocket:
    deadline = time.monotonic() + timeout
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE  # Local self-signed benchmark cert.
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(f"UnrealIRCd exited during TLS startup ({proc.returncode})")
        try:
            raw = socket.create_connection((HOST, 6697), timeout=1.0)
            wrapped = context.wrap_socket(raw, server_hostname="localhost")
            wrapped.settimeout(0.5)
            return wrapped
        except OSError:
            time.sleep(0.1)
    raise TimeoutError("UnrealIRCd did not listen on loopback TLS/6697")


def exchange(sock: socket.socket, data: bytes, expect_welcome: bool = False) -> bytes:
    sock.sendall(data)
    transcript = bytearray()
    hard_deadline = time.monotonic() + (20.0 if expect_welcome else 8.0)
    quiet_deadline = hard_deadline if expect_welcome else time.monotonic() + 3.0
    saw_welcome = not expect_welcome
    while time.monotonic() < hard_deadline:
        try:
            part = sock.recv(65536)
        except socket.timeout:
            if saw_welcome and time.monotonic() >= quiet_deadline:
                break
            continue
        except ConnectionResetError:
            break
        if not part:
            break
        transcript.extend(part)
        # UnrealIRCd may issue its keepalive challenge before registration is
        # complete. Reply as a normal IRC client before waiting for numeric 001.
        for line in part.splitlines():
            fields = line.split()
            try:
                ping_index = fields.index(b"PING")
            except ValueError:
                continue
            if ping_index + 1 < len(fields):
                token = fields[ping_index + 1].lstrip(b":")
                sock.sendall(b"PONG :" + token + b"\r\n")
        if expect_welcome and re.search(rb"(?:^|\s)001(?:\s|$)", transcript):
            saw_welcome = True
        if saw_welcome:
            quiet_deadline = time.monotonic() + 0.5
    return bytes(transcript)


def run_variant(variant: str, out: Path) -> dict:
    prefix = Path(f"/opt/unreal-{variant}")
    log_path = out / f"{variant}.server.log"
    with log_path.open("wb") as log:
        proc = subprocess.Popen(
            [str(prefix / "bin/unrealircd"), "-F", "-f",
             str(prefix / "conf/unrealircd.conf")],
            cwd=prefix, stdout=log, stderr=subprocess.STDOUT,
            env=dict(os.environ),
        )
        result = {}
        try:
            for name, (registration, commands) in CASES.items():
                with connect(proc) as sock:
                    transcript = exchange(sock, registration, expect_welcome=True)
                    if not re.search(rb"(?:^|\s)001(?:\s|$)", transcript):
                        codes = [int(v) for v in NUMERIC.findall(transcript)]
                        raise RuntimeError(
                            f"{variant}/{name}: missing IRC welcome 001; "
                            f"codes={codes}, transcript={transcript[:600]!r}")
                    if commands:
                        transcript += exchange(sock, commands)
                codes = [int(v) for v in NUMERIC.findall(transcript)]
                if not transcript or 1 not in codes:
                    raise RuntimeError(
                        f"{variant}/{name}: missing IRC welcome 001; "
                        f"codes={codes}, transcript={transcript[:600]!r}")
                result[name] = {"numeric_replies": codes,
                                "response_bytes": len(transcript)}
            with connect_tls(proc) as sock:
                transcript = exchange(
                    sock,
                    b"NICK tlstest\r\nUSER tlstest 0 * :TLS Benchmark\r\n",
                    expect_welcome=True,
                )
            codes = [int(v) for v in NUMERIC.findall(transcript)]
            if not transcript or 1 not in codes:
                raise RuntimeError(
                    f"{variant}/TLS: missing IRC welcome 001; codes={codes}, "
                    f"transcript={transcript[:600]!r}")
            result["tls-registration"] = {
                "numeric_replies": codes, "response_bytes": len(transcript)}
        finally:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=8)
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
    numeric = lambda variants: {
        variant: {name: case["numeric_replies"] for name, case in cases.items()}
        for variant, cases in variants.items()
    }
    if numeric(result)["reference"] != numeric(result)["afl"] or numeric(result)["reference"] != numeric(result)["gcov"]:
        (out / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
        raise SystemExit("reference/AFL/gcov IRC reply paths differ; see summary.json")
    (out / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"variants": list(result), "cases": len(CASES),
                      "replies": result["reference"]}, indent=2))
    print("PASS: UnrealIRCd 6.2.7.1 reference/AFL/gcov IRC reply paths match.")


if __name__ == "__main__":
    main()
