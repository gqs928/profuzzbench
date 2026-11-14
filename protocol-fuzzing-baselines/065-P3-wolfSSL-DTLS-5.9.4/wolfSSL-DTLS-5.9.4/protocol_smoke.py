#!/usr/bin/env python3
"""Verify wolfSSL's official DTLS 1.2 UDP echo example with a local client."""
from __future__ import annotations
import argparse, hashlib, json, os, selectors, signal, socket, subprocess, sys, tempfile, time
from pathlib import Path

SERVER = "/opt/wolfssl/bin/server"
CLIENT = "/usr/bin/openssl"
CERT_DIR = os.environ.get("WOLFSSL_CERT_DIR", "/run/wolfssl-benchmark")

def udp_bound(port: int) -> bool:
    result = subprocess.run(["ss", "-lunH"], capture_output=True, text=True, check=False)
    return any(len(row := line.split()) >= 4 and row[3].endswith(f":{port}")
               for line in result.stdout.splitlines())

def server_args(port: int) -> list[str]:
    return [SERVER, "-u", "-v", "3", "-e", "-C", "1", "-p", str(port), "-d",
            "-c", f"{CERT_DIR}/server.crt", "-k", f"{CERT_DIR}/server.key"]

def once(host: str, port: int, index: int) -> dict[str, object]:
    marker = f"wolfSSL-DTLS-echo-probe-{index}"
    with tempfile.TemporaryFile(mode="w+b") as server_log:
        target = subprocess.Popen(server_args(port), stdout=server_log, stderr=subprocess.STDOUT,
                                  start_new_session=True)
        client = None
        try:
            deadline = time.monotonic() + 8
            while time.monotonic() < deadline:
                if target.poll() is not None:
                    server_log.seek(0)
                    raise RuntimeError(f"wolfSSL server exited with {target.returncode}: "
                                       f"{server_log.read().decode(errors='replace')[-2000:]}")
                if udp_bound(port):
                    break
                time.sleep(0.05)
            else:
                raise RuntimeError(f"wolfSSL server did not bind UDP/{port}")

            client = subprocess.Popen(
                [CLIENT, "s_client", "-dtls1_2", "-brief", "-ign_eof",
                 "-connect", f"{host}:{port}", "-servername", "localhost"],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                start_new_session=True)
            assert client.stdin and client.stdout
            client.stdin.write((marker + "\n").encode())
            client.stdin.flush()
            client.stdin.close()
            output = bytearray()
            selector = selectors.DefaultSelector()
            selector.register(client.stdout, selectors.EVENT_READ)
            deadline = time.monotonic() + 15
            while time.monotonic() < deadline:
                if b"CONNECTION ESTABLISHED" in output and marker.encode() in output:
                    break
                events = selector.select(min(0.25, max(0.0, deadline-time.monotonic())))
                for key, _ in events:
                    chunk = os.read(key.fd, 4096)
                    if chunk:
                        output.extend(chunk)
                    else:
                        selector.unregister(key.fileobj)
                if client.poll() is not None and not events:
                    break
            selector.close()
            combined = bytes(output).decode(errors="replace")
            handshake = "CONNECTION ESTABLISHED" in combined
            echoed = marker in combined
            if not handshake or not echoed:
                server_log.flush()
                server_log.seek(0)
                target_log = server_log.read().decode(errors="replace")[-3000:]
                raise RuntimeError(f"wolfSSL DTLS handshake/echo missing for {marker}; "
                                   f"client={combined[-3000:]} target={target_log}")
            if client.poll() is None:
                try:
                    os.killpg(client.pid, signal.SIGINT)
                except ProcessLookupError:
                    pass
                try:
                    client.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    os.killpg(client.pid, signal.SIGKILL)
                    client.wait()
            return {"index": index, "host": host, "port": port,
                    "handshake_complete": handshake, "input_marker": marker,
                    "echo_received": echoed, "client_exit_code": client.returncode,
                    "client_output_sha256": hashlib.sha256(bytes(output)).hexdigest()}
        finally:
            if client is not None and client.poll() is None:
                try:
                    os.killpg(client.pid, signal.SIGINT)
                except ProcessLookupError:
                    pass
                try:
                    client.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    try:
                        os.killpg(client.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    client.wait()
            if target.poll() is None:
                try:
                    os.killpg(target.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                try:
                    target.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    try:
                        os.killpg(target.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    target.wait()

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=int(os.environ.get("WOLFSSL_PORT", "20220")))
    parser.add_argument("--passes", type=int, default=3)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    subprocess.run(["/bin/bash", "/opt/benchmark/prepare-target.sh"], check=True,
                   capture_output=True, text=True, timeout=10)
    rows = [once(args.host, args.port, i + 1) for i in range(args.passes)]
    report = {"target": "wolfSSL 5.9.4 examples/server", "protocol": "DTLS 1.2/UDP",
              "passes": len(rows), "handshakes_complete": all(r["handshake_complete"] for r in rows),
              "echoes_received": all(r["echo_received"] for r in rows), "checks": rows}
    payload = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(f"PASS: {len(rows)} wolfSSL DTLS 1.2 handshakes; echo replies={sum(bool(r['echo_received']) for r in rows)}")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, subprocess.TimeoutExpired, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
