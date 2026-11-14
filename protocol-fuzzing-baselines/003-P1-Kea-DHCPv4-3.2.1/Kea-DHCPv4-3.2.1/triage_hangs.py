#!/usr/bin/env python3
"""Replay Kea DHCPv4 hang candidates against fresh real server processes."""

import collections
import json
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

from make_seeds import packet

SERVER = ("127.0.0.1", 6767)
UDP4_MAX_PAYLOAD = 65507


def dhcp_type(data):
    if len(data) < 240 or data[236:240] != bytes((99, 130, 83, 99)):
        return None
    offset = 240
    while offset < len(data):
        code = data[offset]
        offset += 1
        if code == 255:
            return None
        if code == 0:
            continue
        if offset >= len(data):
            return None
        size = data[offset]
        offset += 1
        if size > len(data) - offset:
            return None
        if code == 53 and size == 1:
            return data[offset]
        offset += size
    return None


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


def wait_ready(proc, log_path, timeout=15.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            return False
        try:
            if "DHCP4_STARTED" in log_path.read_text(errors="replace"):
                return True
        except FileNotFoundError:
            pass
        time.sleep(0.1)
    return False


def send(payload, timeout):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        # Kea's UDP socket mode replies to the relay agent on port 67.
        sock.bind(("127.0.0.1", 67))
        sock.settimeout(timeout)
        sock.sendto(payload, SERVER)
        try:
            data, _ = sock.recvfrom(65535)
            return data
        except socket.timeout:
            return None


def health_probe(proc, candidate, repeat, timeout=2.0):
    if proc.poll() is not None:
        return None
    mac = bytes((2, 0, 0, 1, candidate % 255, repeat))
    xid = 0x48454100 | ((candidate & 255) << 4) | repeat
    payload = packet(1, xid, mac)
    deadline = time.monotonic() + timeout
    response = None
    while time.monotonic() < deadline and proc.poll() is None:
        remaining = max(0.05, deadline - time.monotonic())
        response = send(payload, min(0.25, remaining))
        if response is not None:
            break
    return response


def replay(candidate, out_dir, repeat, index):
    log_path = out_dir / f"{candidate.name}.repeat-{repeat}.kea.log"
    proc, log = start_server(log_path)
    is_ready = wait_ready(proc, log_path)
    payload = candidate.read_bytes()
    record = {
        "candidate": candidate.name,
        "repeat": repeat,
        "candidate_bytes": len(payload),
        "ready_before_replay": is_ready,
        "candidate_sent": False,
    }
    try:
        if is_ready:
            if len(payload) > UDP4_MAX_PAYLOAD:
                record["candidate_send_error"] = f"exceeds IPv4 UDP payload limit of {UDP4_MAX_PAYLOAD} bytes"
            else:
                start = time.monotonic()
                try:
                    response = send(payload, 5.0)
                    record["candidate_sent"] = True
                    record["candidate_wait_seconds"] = round(time.monotonic() - start, 3)
                    record["candidate_response_bytes"] = None if response is None else len(response)
                    record["candidate_response_dhcp_type"] = None if response is None else dhcp_type(response)
                except OSError as exc:
                    record["candidate_send_error"] = f"{type(exc).__name__}: {exc}"
        record["target_exit_before_health"] = proc.poll()
        record["target_alive_before_cleanup"] = proc.poll() is None
        health = health_probe(proc, int(index), repeat)
        record["health_response_bytes"] = None if health is None else len(health)
        record["health_response_dhcp_type"] = None if health is None else dhcp_type(health)
        record["health_probe_passed"] = record["health_response_dhcp_type"] in (2, 5)
        if not is_ready:
            record["classification"] = "service_not_ready"
        elif record.get("candidate_send_error", "").startswith("exceeds IPv4 UDP payload"):
            record["classification"] = "unreplayable_udp_datagram_exceeds_limit"
        elif record["target_exit_before_health"] is not None:
            record["classification"] = "target_exited_before_cleanup"
        elif record["target_alive_before_cleanup"] and record["health_probe_passed"]:
            record["classification"] = "target_survived_and_health_probe_passed"
        else:
            record["classification"] = "service_unresponsive_candidate"
        record["target_exit_after_cleanup"] = None
        if proc.poll() is None:
            try:
                os.killpg(proc.pid, signal.SIGTERM)
                record["target_exit_after_cleanup"] = proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                record["target_exit_after_cleanup"] = proc.wait(timeout=2)
        else:
            record["target_exit_after_cleanup"] = proc.returncode
        record["log"] = log_path.name
        return record
    finally:
        if proc.poll() is None:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait(timeout=2)
            except ProcessLookupError:
                pass
        log.close()


def main():
    if len(sys.argv) != 4:
        raise SystemExit("usage: triage_hangs.py CANDIDATE_DIR OUTPUT_DIR REPEATS")
    candidates = Path(sys.argv[1])
    out_dir = Path(sys.argv[2])
    repeats = int(sys.argv[3])
    out_dir.mkdir(parents=True, exist_ok=True)
    items = sorted(path for path in candidates.iterdir() if path.is_file())
    records = []
    with (out_dir / "triage-records.jsonl").open("w") as stream:
        for index, candidate in enumerate(items, 1):
            for repeat in range(1, repeats + 1):
                record = replay(candidate, out_dir, repeat, index)
                records.append(record)
                stream.write(json.dumps(record, sort_keys=True) + "\n")
                stream.flush()
    counts = collections.Counter(record["classification"] for record in records)
    summary = {
        "protocol": "DHCPv4/UDP",
        "implementation": "Kea 3.2.1",
        "method": "fresh Kea DHCPv4 process per candidate replay; follow with a valid DHCPDISCOVER/DHCPOFFER health check; do not truncate UDP payloads",
        "candidate_count": len(items),
        "repetitions_per_candidate": repeats,
        "records": records,
        "classification_counts": dict(counts),
    }
    (out_dir / "triage-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary["classification_counts"], sort_keys=True))


if __name__ == "__main__":
    main()
