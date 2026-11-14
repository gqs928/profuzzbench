#!/usr/bin/env python3
"""Smoke-test real Kea DHCPv4 offers across fresh server processes."""

import argparse
import json
import os
import signal
import socket
import subprocess
import time
from pathlib import Path

from make_seeds import packet

SERVER = ("127.0.0.1", 6767)


def options(data):
    if len(data) < 240 or data[236:240] != bytes((99, 130, 83, 99)):
        return {}
    found = {}
    offset = 240
    while offset < len(data):
        code = data[offset]
        offset += 1
        if code == 255:
            break
        if code == 0:
            continue
        if offset >= len(data):
            break
        length = data[offset]
        offset += 1
        if length > len(data) - offset:
            break
        found.setdefault(code, []).append(data[offset:offset + length])
        offset += length
    return found


def start_server(log_path):
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log = log_path.open("wb")
    env = {
        **os.environ,
    }
    proc = subprocess.Popen(
        ["/work/kea-target.sh"],
        cwd="/work", stdout=log, stderr=subprocess.STDOUT,
        env=env, start_new_session=True,
    )
    return proc, log


def stop_server(proc, log):
    if proc.poll() is None:
        try:
            os.killpg(proc.pid, signal.SIGTERM)
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait(timeout=2)
    log.close()


def exchange(payload, timeout):
    started = time.monotonic()
    response = None
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        # Kea's UDP socket mode replies to the DHCP relay address on port 67.
        sock.bind(("127.0.0.1", 67))
        sock.settimeout(0.25)
        deadline = started + timeout
        while time.monotonic() < deadline:
            sock.sendto(payload, SERVER)
            try:
                response, _ = sock.recvfrom(65535)
                break
            except socket.timeout:
                pass
    return response, round(time.monotonic() - started, 3)


def run_once(repeat, timeout):
    log_path = Path(f"/work/results/build/smoke/repeat-{repeat}.kea.log")
    proc, log = start_server(log_path)
    mac = bytes((2, 0, 0, 0, 0, repeat))
    discover = packet(1, 0x4B454100 + repeat, mac)
    try:
        if proc.poll() is not None:
            raise RuntimeError(f"Kea exited {proc.returncode} before replying; see {log_path}")
        offer, offer_elapsed = exchange(discover, timeout)
        if offer is None:
            raise TimeoutError(f"no DHCPOFFER within {timeout}s; see {log_path}")
        offer_types = options(offer).get(53, [])
        if offer[0] != 2 or offer_types != [bytes((2,))]:
            raise RuntimeError(f"expected BOOTREPLY/DHCPOFFER, got op={offer[0]} type={offer_types!r}")
        offered_ip = socket.inet_ntoa(offer[16:20])

        request = packet(
            3, 0x4B455200 + repeat, mac,
            extra=[(50, socket.inet_aton(offered_ip)), (54, socket.inet_aton("127.0.0.1"))],
        )
        ack, ack_elapsed = exchange(request, timeout)
        if ack is None:
            raise TimeoutError(f"no DHCPACK within {timeout}s after DHCPOFFER; see {log_path}")
        ack_types = options(ack).get(53, [])
        if ack[0] != 2 or ack_types != [bytes((5,))]:
            raise RuntimeError(f"expected BOOTREPLY/DHCPACK, got op={ack[0]} type={ack_types!r}")
        return {
            "repeat": repeat,
            "offer_bytes": len(offer),
            "offer_dhcp_message_type": offer_types[0][0],
            "offer_xid": offer[4:8].hex(),
            "offered_yiaddr": offered_ip,
            "offer_elapsed_seconds": offer_elapsed,
            "ack_bytes": len(ack),
            "ack_dhcp_message_type": ack_types[0][0],
            "ack_xid": ack[4:8].hex(),
            "ack_yiaddr": socket.inet_ntoa(ack[16:20]),
            "ack_elapsed_seconds": ack_elapsed,
            "target_alive_before_cleanup": proc.poll() is None,
            "log": log_path.name,
        }
    finally:
        stop_server(proc, log)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int, default=10)
    parser.add_argument("--timeout", type=float, default=10.0)
    args = parser.parse_args()
    records = [run_once(i, args.timeout) for i in range(1, args.repeats + 1)]
    transcripts = {
        (r["offer_dhcp_message_type"], r["offered_yiaddr"], r["ack_dhcp_message_type"], r["ack_yiaddr"])
        for r in records
    }
    if transcripts != {(2, "127.0.0.100", 5, "127.0.0.100")}:
        raise SystemExit(f"fresh-process DHCP DORA transcript varied: {sorted(transcripts)}")
    result = {
        "protocol": "DHCPv4/UDP",
        "implementation": "Kea 3.2.1",
        "server_port": 6767,
        "fresh_process_repetitions": args.repeats,
        "response_status": "DHCPOFFER then DHCPACK",
        "stable_yiaddr": "127.0.0.100",
        "pass": True,
        "records": records,
    }
    out = Path("/work/results/build/service-smoke.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "records"}, sort_keys=True))


if __name__ == "__main__":
    main()
