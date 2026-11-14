#!/usr/bin/env python3
"""Start fresh OpenSSL DTLS servers and verify handshake plus reverse-echo."""
from __future__ import annotations
import argparse, hashlib, json, os, signal, socket, subprocess, sys, tempfile, time
from pathlib import Path

OPENSSL = "/opt/openssl/bin/openssl"
TARGET = "/opt/openssl/bin/dtls_echo_server"
CERT_DIR = os.environ.get("OPENSSL_CERT_DIR", "/run/openssl-dtls-benchmark")

def udp_bound(port: int) -> bool:
    result = subprocess.run(["ss", "-lunH"], capture_output=True, text=True, check=False)
    return any(line.split()[3].endswith(f":{port}") for line in result.stdout.splitlines()
               if len(line.split()) >= 5)

def once(host: str, port: int, index: int) -> dict[str, object]:
    marker = f"OpenSSL-DTLS-probe-{index}"
    server = [TARGET, "--port", str(port), "--cert", f"{CERT_DIR}/server.crt",
              "--key", f"{CERT_DIR}/server.key"]
    with tempfile.TemporaryFile(mode="w+b") as log:
        target = subprocess.Popen(server, stdout=log, stderr=subprocess.STDOUT,
                                   start_new_session=True)
        try:
            deadline = time.monotonic() + 8
            while time.monotonic() < deadline:
                if target.poll() is not None:
                    log.seek(0)
                    raise RuntimeError(f"dtls_echo_server exited with {target.returncode}: "
                                       f"{log.read().decode(errors='replace')[-2000:]}")
                if udp_bound(port):
                    break
                time.sleep(0.05)
            else:
                raise RuntimeError(f"DTLS echo target did not bind UDP/{port}")
            # Keep the DTLS session open after the probe input reaches EOF so
            # the target can return its application-data echo before shutdown.
            client = [OPENSSL, "s_client", "-dtls1_2", "-brief", "-ign_eof",
                      "-connect", f"{host}:{port}", "-servername", "localhost"]
            proc = subprocess.run(client, input=marker + "\n", capture_output=True,
                                  text=True, timeout=20, check=False)
            combined = proc.stdout + proc.stderr
            log.flush()
            log.seek(0)
            target_log = log.read().decode(errors="replace")[-3000:]
            handshake = "CONNECTION ESTABLISHED" in combined
            reverse_echo = marker[::-1] in combined
            if not handshake:
                raise RuntimeError(f"DTLS 1.2 handshake not confirmed (exit={proc.returncode}): "
                                   f"client={combined[-2000:]} target={target_log}")
            if not reverse_echo:
                raise RuntimeError(f"DTLS reverse-echo response not found for {marker}: "
                                   f"client={combined[-2000:]} target={target_log}")
            return {"index": index, "host": host, "port": port,
                    "client_exit_code": proc.returncode, "handshake_complete": handshake,
                    "input_marker": marker, "reverse_echo": marker[::-1],
                    "echo_received": reverse_echo, "client_bytes": len(marker) + 1,
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
    parser.add_argument("--port", type=int, default=int(os.environ.get("OPENSSL_PORT", "20220")))
    parser.add_argument("--passes", type=int, default=3)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    subprocess.run(["/bin/bash", "/opt/benchmark/prepare-target.sh"], check=True,
                   capture_output=True, text=True, timeout=10)
    rows = [once(args.host, args.port, i + 1) for i in range(args.passes)]
    report = {"target": "OpenSSL 4.1.0 instrumented DTLS echo harness", "protocol": "DTLS 1.2/UDP",
              "passes": len(rows), "handshakes_complete": all(r["handshake_complete"] for r in rows),
              "reverse_echoes_received": all(r["echo_received"] for r in rows), "checks": rows}
    payload = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(f"PASS: {len(rows)} OpenSSL DTLS 1.2 handshakes; reverse replies={sum(bool(r['echo_received']) for r in rows)}")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, subprocess.TimeoutExpired, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
