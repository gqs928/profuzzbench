#!/usr/bin/env python3
"""Verify LSQUIC http_server responds to a valid QUIC v1 Initial."""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import signal
import socket
import subprocess
import time


def packet_kind(data: bytes) -> str:
    if not data:
        return "empty"
    if not data[0] & 0x80:
        return "short-header"
    if len(data) < 7:
        return "truncated-long-header"
    version = int.from_bytes(data[1:5], "big")
    if version == 0:
        return "version-negotiation"
    packet_type = (data[0] >> 4) & 3
    if version == 1:
        return ("initial", "0-rtt", "handshake", "retry")[packet_type]
    if version == 0x6B3343CF:
        return ("retry", "initial", "0-rtt", "handshake")[packet_type]
    return f"long-header-version-{version:08x}-type-{packet_type}"


def server_command(port: int) -> list[str]:
    return [
        os.environ.get("LSQUIC_SERVER", "/opt/benchmark/http_server"),
        "-c", f"quic.tech,{os.environ.get('LSQUIC_CERT', '/opt/benchmark/certs/server.crt')},"
              f"{os.environ.get('LSQUIC_KEY', '/opt/benchmark/certs/server.key')}",
        "-r", os.environ.get("LSQUIC_ROOT", "/opt/benchmark/www"),
        "-s", f"127.0.0.1:{port}",
        "-L", "error",
    ]


def port_is_free(port: int) -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.bind(("127.0.0.1", port))
        return True
    except OSError:
        return False
    finally:
        sock.close()


def wait_bound(proc: subprocess.Popen[bytes], port: int, timeout: float) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            return False
        if not port_is_free(port):
            return True
        time.sleep(0.01)
    return False


def one_pass(seed: bytes, port: int, timeout: float) -> dict[str, object]:
    proc = subprocess.Popen(server_command(port), stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, start_new_session=True)
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client.settimeout(0.2)
    response = b""
    error = None
    try:
        if not wait_bound(proc, port, 5):
            raise RuntimeError(f"LSQUIC http_server did not bind UDP/{port}")
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if proc.poll() is not None:
                raise RuntimeError(f"http_server exited during startup: {proc.returncode}")
            try:
                client.sendto(seed, ("127.0.0.1", port))
                response, _ = client.recvfrom(65535)
                break
            except socket.timeout:
                continue
        if not response:
            raise RuntimeError("server returned no QUIC response to valid Initial")
        kind = packet_kind(response)
        if kind not in ("initial", "handshake", "retry", "version-negotiation"):
            raise RuntimeError(f"unexpected QUIC response packet type: {kind}")
        if proc.poll() is not None:
            raise RuntimeError(f"http_server exited after processing Initial: {proc.returncode}")
    except Exception as exc:
        error = str(exc)
    finally:
        client.close()
        if proc.poll() is None:
            proc.send_signal(signal.SIGTERM)
        try:
            exit_code = proc.wait(timeout=4)
        except subprocess.TimeoutExpired:
            proc.kill()
            exit_code = proc.wait(timeout=2)
    stdout, stderr = proc.communicate(timeout=2)
    released = port_is_free(port)
    result: dict[str, object] = {
        "seed_bytes": len(seed),
        "request_packet_type": packet_kind(seed),
        "response_bytes": len(response),
        "response_packet_type": packet_kind(response),
        "server_alive_after_request": error is None,
        "controlled_exit_code": exit_code,
        "server_exit_after_controlled_sigterm": exit_code in (0, -signal.SIGTERM),
        "listener_released": released,
    }
    if error:
        result["error"] = error
        result["server_stdout_tail"] = stdout.decode(errors="replace")[-3000:]
        result["server_stderr_tail"] = stderr.decode(errors="replace")[-6000:]
    if error or not result["server_exit_after_controlled_sigterm"] or not released:
        raise RuntimeError(json.dumps(result, indent=2))
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=pathlib.Path,
                        default=pathlib.Path("/opt/benchmark/seeds/quic-v1-client-initial.bin"))
    parser.add_argument("--port", type=int, default=4433)
    parser.add_argument("--passes", type=int, default=3)
    parser.add_argument("--timeout", type=float, default=3)
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()
    seed = args.seed.read_bytes()
    if not 1200 <= len(seed) <= 65507:
        raise SystemExit(f"invalid seed datagram size: {len(seed)}")
    checks = [one_pass(seed, args.port + index, args.timeout) for index in range(args.passes)]
    report = {
        "target": "LSQUIC v4.11.1 http_server",
        "transport": "QUIC v1 over UDP",
        "scope": "valid client Initial processing and first server packet; no completed HTTP/3 exchange",
        "seed_provenance": "generated by Cloudflare quiche 0.30.0 with SNI quic.tech",
        "passes": args.passes,
        "all_responses_valid": True,
        "checks": checks,
    }
    rendered = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, ValueError) as exc:
        raise SystemExit(f"LSQUIC smoke failed: {exc}")
