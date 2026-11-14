#!/usr/bin/env python3
"""Replay UDP queue samples against a fresh quiche-server process per sample."""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import signal
import socket
import subprocess
import time
from collections import Counter


def server_command(port: int) -> list[str]:
    return [
        os.environ.get("QUICHE_SERVER", "/opt/quiche/target/release/quiche-server"),
        "--listen", f"127.0.0.1:{port}",
        "--cert", os.environ.get("QUICHE_CERT", "/opt/quiche/apps/src/bin/cert.crt"),
        "--key", os.environ.get("QUICHE_KEY", "/opt/quiche/apps/src/bin/cert.key"),
        "--root", os.environ.get("QUICHE_ROOT", "/opt/benchmark/www"),
        "--no-retry", "--disable-gso", "--disable-pacing",
    ]


def wait_bound(proc: subprocess.Popen[bytes], port: int, timeout: float) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            return False
        probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            probe.bind(("127.0.0.1", port))
            bound = False
        except OSError:
            bound = True
        finally:
            probe.close()
        if bound:
            return True
        time.sleep(0.01)
    return False


def port_free(port: int) -> bool:
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        probe.bind(("127.0.0.1", port))
        return True
    except OSError:
        return False
    finally:
        probe.close()


def replay(path: pathlib.Path, port: int, response_timeout: float) -> dict[str, object]:
    data = path.read_bytes()
    row: dict[str, object] = {"file": path.name, "bytes": len(data)}
    env = os.environ.copy()
    env["RUST_LOG"] = "error"
    proc = subprocess.Popen(server_command(port), stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL, start_new_session=True, env=env)
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client.settimeout(response_timeout)
    response = b""
    startup_ok = wait_bound(proc, port, 2.0)
    if startup_ok:
        try:
            client.sendto(data, ("127.0.0.1", port))
            response, _ = client.recvfrom(65535)
        except socket.timeout:
            pass
        except OSError as exc:
            row["transport_error"] = f"{type(exc).__name__}: {exc}"
    alive_after = proc.poll() is None
    if alive_after:
        proc.send_signal(signal.SIGTERM)
    try:
        exit_code = proc.wait(timeout=2)
    except subprocess.TimeoutExpired:
        proc.kill()
        exit_code = proc.wait(timeout=2)
    client.close()
    released = port_free(port)
    row.update({
        "target_started": startup_ok,
        "target_exit_before_cleanup": None if alive_after else proc.returncode,
        "target_alive_after_input": alive_after,
        "controlled_exit_code": exit_code,
        "clean_sigterm_exit": alive_after and exit_code in (0, -signal.SIGTERM),
        "target_exit_after_cleanup": exit_code,
        "listener_released": released,
        "response_bytes": len(response),
        "response_header_type": (
            "empty" if not response else
            "short" if not response[0] & 0x80 else
            "truncated-long" if len(response) < 7 else
            f"long-v{int.from_bytes(response[1:5], 'big'):08x}-type-{(response[0] >> 4) & 3}"
        ),
    })
    return row


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("queue", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    parser.add_argument("--port", type=int, default=46000)
    parser.add_argument("--response-timeout", type=float, default=0.05)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--allow-target-exit", action="store_true",
                        help="record, but do not reject, a target exit (for AFLNet crash/hang triage)")
    args = parser.parse_args()
    files = sorted(p for p in args.queue.iterdir() if p.is_file() and not p.name.startswith("."))
    if args.limit is not None:
        files = files[:args.limit]
    rows = [replay(path, args.port + (index % 1000), args.response_timeout)
            for index, path in enumerate(files)]
    summary = {
        "queue": str(args.queue),
        "samples_total": len(rows),
        "target_started": sum(bool(row["target_started"]) for row in rows),
        "target_alive_after_input": sum(bool(row["target_alive_after_input"]) for row in rows),
        "clean_sigterm_exit": sum(bool(row["clean_sigterm_exit"]) for row in rows),
        "unexpected_exit_before_cleanup": sum(not bool(row["target_alive_after_input"]) for row in rows),
        "listeners_released": sum(bool(row["listener_released"]) for row in rows),
        "no_response": sum(int(row["response_bytes"]) == 0 for row in rows),
        "response_header_types": dict(Counter(str(row["response_header_type"]) for row in rows)),
        "records": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in summary.items() if key != "records"}, indent=2))
    if any(not row["target_started"] or not row["listener_released"] or
           (not args.allow_target_exit and
            (not row["target_alive_after_input"] or not row["clean_sigterm_exit"]))
           for row in rows):
        raise SystemExit("queue replay found a server crash, stuck process, or unreleased UDP listener")


if __name__ == "__main__":
    main()
