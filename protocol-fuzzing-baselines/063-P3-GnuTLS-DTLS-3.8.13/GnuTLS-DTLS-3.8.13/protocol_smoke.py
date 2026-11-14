#!/usr/bin/env python3
"""Start fresh GnuTLS server processes and verify DTLS 1.2 handshakes and echo."""
from __future__ import annotations
import argparse, hashlib, json, os, signal, socket, subprocess, sys, tempfile, time
from pathlib import Path

PRIORITY = "NORMAL:-VERS-ALL:+VERS-DTLS1.2"
SERVER = "/opt/gnutls/bin/gnutls-serv"
CLIENT = "/opt/gnutls/bin/gnutls-cli"
CERT_DIR = os.environ.get("GNUTLS_CERT_DIR", "/run/gnutls-benchmark")

def udp_bound(port: int) -> bool:
    result = subprocess.run(["ss", "-lunH"], capture_output=True, text=True, check=False)
    return any(line.split()[3].endswith(f":{port}") for line in result.stdout.splitlines()
               if len(line.split()) >= 5)

def once(host: str, port: int, index: int) -> dict[str, object]:
    marker = f"DTLS-echo-probe-{index}"
    server = [SERVER, "--udp", "--nocookie", f"--port={port}", "--echo",
              f"--priority={PRIORITY}", f"--x509keyfile={CERT_DIR}/server.key",
              f"--x509certfile={CERT_DIR}/server.crt"]
    with tempfile.TemporaryFile(mode="w+b") as log:
        target = subprocess.Popen(server, stdout=log, stderr=subprocess.STDOUT,
                                   start_new_session=True)
        try:
            deadline = time.monotonic() + 8
            while time.monotonic() < deadline:
                if target.poll() is not None:
                    log.seek(0)
                    raise RuntimeError(f"gnutls-serv exited with {target.returncode}: {log.read().decode(errors='replace')[-2000:]}")
                if udp_bound(port):
                    break
                time.sleep(0.05)
            else:
                raise RuntimeError(f"gnutls-serv did not bind UDP/{port}")
            client = [CLIENT, "--udp", "--insecure", "--priority", PRIORITY,
                      "--port", str(port), host]
            proc = subprocess.run(client, input=marker + "\n", capture_output=True,
                                  text=True, timeout=15, check=False)
            combined = proc.stdout + proc.stderr
            if "Handshake was completed" not in combined:
                raise RuntimeError(f"DTLS handshake was not confirmed (exit={proc.returncode}): {combined[-3000:]}")
            echoed = marker in combined
            return {"index": index, "host": host, "port": port,
                    "client_exit_code": proc.returncode, "handshake_complete": True,
                    "echo_marker": marker, "echo_received": echoed,
                    "client_bytes": len(marker) + 1, "priority": PRIORITY,
                    "stdout_sha256": hashlib.sha256(proc.stdout.encode()).hexdigest()}
        finally:
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
    parser.add_argument("--port", type=int, default=int(os.environ.get("GNUTLS_PORT", "20220")))
    parser.add_argument("--passes", type=int, default=3)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    subprocess.run(["/bin/bash", "/opt/benchmark/prepare-target.sh"], check=True,
                   capture_output=True, text=True, timeout=10)
    rows = [once(args.host, args.port, i + 1) for i in range(args.passes)]
    report = {"target": "GnuTLS 3.8.13 gnutls-serv", "protocol": "DTLS 1.2/UDP",
              "passes": len(rows), "handshakes_complete": all(r["handshake_complete"] for r in rows),
              "echoes_received": all(r["echo_received"] for r in rows), "checks": rows}
    payload = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(f"PASS: {len(rows)} DTLS 1.2 full handshakes; echo replies={sum(bool(r['echo_received']) for r in rows)}")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, subprocess.TimeoutExpired, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
