#!/usr/bin/env python3
"""Independently replay AFLNet DNS/UDP hang candidates against fresh named processes."""

import json
import os
import socket
import struct
import subprocess
import sys
import time
from pathlib import Path


def dns_query(txid=0x7A31):
    labels = (b"www", b"example", b"test")
    qname = b"".join(bytes((len(label),)) + label for label in labels) + b"\0"
    return struct.pack("!HHHHHH", txid, 0x0100, 1, 0, 0, 0) + qname + struct.pack("!HH", 1, 1)


def healthy_query(timeout=1.0):
    payload = dns_query()
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(timeout)
        sock.sendto(payload, ("127.0.0.1", 5353))
        try:
            data, _ = sock.recvfrom(4096)
        except socket.timeout:
            return False
    return len(data) >= 12 and data[:2] == payload[:2] and bool(data[2] & 0x80)


def wait_ready(proc, timeout=10.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            return False
        try:
            if healthy_query(0.25):
                return True
        except OSError:
            pass
        time.sleep(0.1)
    return False


def replay(candidate, out_dir, repeat):
    state_dir = Path("/work/state")
    state_dir.mkdir(parents=True, exist_ok=True)
    for item in state_dir.iterdir():
        if item.is_file() or item.is_symlink():
            item.unlink()
        elif item.is_dir():
            import shutil
            shutil.rmtree(item)

    log_path = out_dir / f"{candidate.name}.repeat-{repeat}.named.log"
    with log_path.open("wb") as log:
        proc = subprocess.Popen(
            ["/opt/bind-afl/sbin/named", "-g", "-c", "/work/named.conf", "-n", "1", "-U", "1"],
            cwd="/work", stdout=log, stderr=subprocess.STDOUT,
            env={**os.environ, "ASAN_OPTIONS": "abort_on_error=1:detect_leaks=0:detect_stack_use_after_return=1:symbolize=0"},
        )
        ready = wait_ready(proc)
        record = {
            "candidate": candidate.name,
            "repeat": repeat,
            "candidate_bytes": candidate.stat().st_size,
            "ready_before_replay": ready,
        }
        if ready:
            payload = candidate.read_bytes()
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.settimeout(5.0)
                start = time.monotonic()
                sock.sendto(payload, ("127.0.0.1", 5353))
                try:
                    response, _ = sock.recvfrom(4096)
                    record["candidate_response_bytes"] = len(response)
                    record["candidate_response_hex"] = response.hex()
                    if len(response) >= 12:
                        ident, flags, qdcount, ancount, nscount, arcount = struct.unpack("!HHHHHH", response[:12])
                        record["candidate_response_id_matches"] = ident == struct.unpack("!H", payload[:2])[0]
                        record["candidate_response_flags"] = f"0x{flags:04x}"
                        record["candidate_response_rcode"] = flags & 0xF
                        record["candidate_response_counts"] = {
                            "question": qdcount, "answer": ancount,
                            "authority": nscount, "additional": arcount,
                        }
                except socket.timeout:
                    record["candidate_response_bytes"] = None
                record["candidate_wait_seconds"] = round(time.monotonic() - start, 3)
            time.sleep(0.2)
        record["target_exit_before_cleanup"] = proc.poll()
        record["target_alive_before_cleanup"] = proc.poll() is None
        record["health_probe_after_candidate"] = healthy_query(1.0) if proc.poll() is None else False
        if proc.poll() is None:
            proc.terminate()
            try:
                record["target_exit_after_cleanup"] = proc.wait(timeout=3.0)
            except subprocess.TimeoutExpired:
                proc.kill()
                record["target_exit_after_cleanup"] = proc.wait(timeout=2.0)
        else:
            record["target_exit_after_cleanup"] = proc.returncode
        record["named_log"] = log_path.name
        if record["target_exit_before_cleanup"] is not None:
            record["classification"] = "target_exited_before_cleanup"
        elif record["target_alive_before_cleanup"] and record["health_probe_after_candidate"]:
            record["classification"] = "target_survived_and_health_probe_passed"
        else:
            record["classification"] = "service_unresponsive_candidate"
        return record


def main():
    if len(sys.argv) != 4:
        raise SystemExit("usage: triage_hangs.py CANDIDATE_DIR OUTPUT_DIR REPEATS")
    candidates = Path(sys.argv[1])
    out_dir = Path(sys.argv[2])
    repeats = int(sys.argv[3])
    out_dir.mkdir(parents=True, exist_ok=True)
    items = sorted(p for p in candidates.iterdir() if p.is_file())
    records = [replay(candidate, out_dir, n) for candidate in items for n in range(1, repeats + 1)]
    summary = {
        "protocol": "DNS/UDP",
        "implementation": "BIND 9.20.30",
        "method": "fresh instrumented named process per candidate replay; follow with valid DNS health query",
        "repetitions_per_candidate": repeats,
        "records": records,
        "classification_counts": {},
    }
    for record in records:
        key = record["classification"]
        summary["classification_counts"][key] = summary["classification_counts"].get(key, 0) + 1
    (out_dir / "triage-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary["classification_counts"], sort_keys=True))


if __name__ == "__main__":
    main()
