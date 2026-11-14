#!/usr/bin/env python3
"""Capture valid DTLS 1.2 ClientHello datagrams from the matching GnuTLS client."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import select
import signal
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

SERVER = "/opt/gnutls/bin/gnutls-serv"
CLIENT = "/opt/gnutls/bin/gnutls-cli"
PRIORITY = "NORMAL:-VERS-ALL:+VERS-DTLS1.2"
CERT_DIR = Path(os.environ.get("GNUTLS_CERT_DIR", "/run/gnutls-benchmark"))


def udp_bound(port: int) -> bool:
    result = subprocess.run(["ss", "-lunH"], capture_output=True, text=True, check=False)
    return any(line.split()[3].endswith(f":{port}") for line in result.stdout.splitlines()
               if len(line.split()) >= 5)


def stop(process: subprocess.Popen[str] | None) -> str:
    if process is None:
        return ""
    if process.poll() is None:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
    return ""


def client_hello(data: bytes) -> bool:
    if len(data) < 25 or data[0] != 22 or data[1:3] != b"\xfe\xfd":
        return False
    record_length = int.from_bytes(data[11:13], "big")
    return record_length >= 12 and len(data) >= 26 and data[13] == 1


def capture_one(index: int, relay: socket.socket, proxy_port: int,
                backend_port: int, outdir: Path) -> dict[str, object]:
    with tempfile.TemporaryFile(mode="w+b") as server_log:
        server = subprocess.Popen(
            [SERVER, "--udp", "--nocookie", f"--port={backend_port}", "--echo",
             f"--priority={PRIORITY}", f"--x509keyfile={CERT_DIR}/server.key",
             f"--x509certfile={CERT_DIR}/server.crt"],
            stdout=server_log, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            deadline = time.monotonic() + 8
            while time.monotonic() < deadline and not udp_bound(backend_port):
                if server.poll() is not None:
                    break
                time.sleep(0.05)
            if not udp_bound(backend_port):
                server_log.seek(0)
                raise RuntimeError(f"GnuTLS server failed to bind UDP/{backend_port}: "
                                   f"{server_log.read().decode(errors='replace')[-1500:]}")

            client = subprocess.Popen(
                [CLIENT, "--udp", "--insecure", "--priority", PRIORITY,
                 "--sni-hostname", f"seed-{index:02d}.localhost",
                 "--port", str(proxy_port), "127.0.0.1"],
                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, text=True, start_new_session=True)
            captured: bytes | None = None
            seen_client_datagrams = 0
            client_addr: tuple[str, int] | None = None
            deadline = time.monotonic() + 20
            try:
                while time.monotonic() < deadline:
                    readable, _, _ = select.select([relay], [], [], 0.05)
                    if readable:
                        packet, sender = relay.recvfrom(65535)
                        if sender == ("127.0.0.1", backend_port):
                            if client_addr:
                                relay.sendto(packet, client_addr)
                        else:
                            client_addr = sender
                            seen_client_datagrams += 1
                            if captured is None and client_hello(packet):
                                captured = packet
                            relay.sendto(packet, ("127.0.0.1", backend_port))
                    if client.poll() is not None:
                        break
                if client.poll() is None:
                    client.terminate()
                    try:
                        client.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        client.kill()
                output = client.communicate(timeout=3)[0]
            finally:
                if client.poll() is None:
                    client.kill()
                    client.wait()

            if captured is None:
                raise RuntimeError(f"GnuTLS client emitted no valid ClientHello: {output[-2000:]}")
            if "Handshake was completed" not in output:
                raise RuntimeError(f"GnuTLS client handshake failed: {output[-2000:]}")
            path = outdir / f"gnutls-clienthello-{index:02d}.raw"
            path.write_bytes(captured)
            return {"file": path.name, "bytes": len(captured),
                    "sha256": hashlib.sha256(captured).hexdigest(),
                    "client_datagrams": seen_client_datagrams,
                    "handshake_complete": True}
        finally:
            stop(server)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--passes", type=int, default=3)
    parser.add_argument("--proxy-port", type=int, default=20220)
    parser.add_argument("--backend-port", type=int, default=20221)
    args = parser.parse_args()
    if args.passes < 1 or args.proxy_port == args.backend_port:
        parser.error("passes must be positive and proxy/backend ports must differ")
    subprocess.run(["/bin/bash", "/opt/benchmark/prepare-target.sh"], check=True,
                   capture_output=True, text=True, timeout=10)
    args.output.mkdir(parents=True, exist_ok=True)
    relay = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    relay.bind(("127.0.0.1", args.proxy_port))
    relay.setblocking(False)
    try:
        records = [capture_one(i + 1, relay, args.proxy_port,
                               args.backend_port, args.output)
                   for i in range(args.passes)]
    finally:
        relay.close()
    report = {"protocol": "DTLS 1.2/UDP", "seed_source": "GnuTLS 3.8.13 gnutls-cli",
              "passes": len(records), "seeds": records}
    (args.output / "capture-manifest.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: captured {len(records)} GnuTLS ClientHello seed(s)")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, subprocess.TimeoutExpired, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
