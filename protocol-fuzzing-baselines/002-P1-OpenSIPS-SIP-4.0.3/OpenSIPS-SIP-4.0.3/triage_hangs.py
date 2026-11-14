#!/usr/bin/env python3
"""Replay AFLNet SIP/UDP hang candidates against fresh OpenSIPS processes."""

import collections
import json
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path


def make_options(call_id):
    return (
        "OPTIONS sip:service@example.test SIP/2.0\r\n"
        "Via: SIP/2.0/UDP 127.0.0.1;branch=z9hG4bKtriage-" + call_id + ";rport\r\n"
        "Max-Forwards: 70\r\n"
        "From: <sip:triage@example.test>;tag=triage\r\n"
        "To: <sip:service@example.test>\r\n"
        "Call-ID: " + call_id + "@benchmark.example\r\n"
        "CSeq: 1 OPTIONS\r\n"
        "Content-Length: 0\r\n\r\n"
    ).encode()


def send_udp(payload, timeout):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(timeout)
        sock.sendto(payload, ("127.0.0.1", 5060))
        try:
            data, _ = sock.recvfrom(65535)
            return data
        except socket.timeout:
            return None


def ready(proc, timeout=15.0):
    deadline = time.monotonic() + timeout
    index = 0
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            return False
        index += 1
        response = send_udp(make_options(f"ready-{index}"), 0.3)
        if response and response.startswith(b"SIP/2.0 200"):
            return True
        time.sleep(0.1)
    return False


def replay(candidate, out_dir, repeat):
    log_path = out_dir / f"{candidate.name}.repeat-{repeat}.opensips.log"
    with log_path.open("wb") as log:
        proc = subprocess.Popen(
            ["/src/opensips/opensips", "-F", "-f", "/work/opensips.cfg", "-s", "F_PARALLEL_MALLOC"],
            cwd="/work", stdout=log, stderr=subprocess.STDOUT,
            env={**os.environ, "ASAN_OPTIONS": "abort_on_error=1:detect_leaks=0:symbolize=0"},
            start_new_session=True,
        )
        is_ready = ready(proc)
        record = {
            "candidate": candidate.name,
            "repeat": repeat,
            "candidate_bytes": candidate.stat().st_size,
            "ready_before_replay": is_ready,
            "candidate_sent": False,
        }
        if is_ready:
            payload = candidate.read_bytes()
            if len(payload) > 65507:
                record["candidate_send_error"] = "candidate exceeds the IPv4 UDP payload limit of 65507 bytes"
            else:
                start = time.monotonic()
                try:
                    response = send_udp(payload, 5.0)
                    record["candidate_sent"] = True
                    record["candidate_wait_seconds"] = round(time.monotonic() - start, 3)
                    record["candidate_response_bytes"] = None if response is None else len(response)
                    record["candidate_response_first_line"] = None if response is None else response.split(b"\r\n", 1)[0].decode("ascii", "replace")
                except OSError as exc:
                    record["candidate_send_error"] = f"{type(exc).__name__}: {exc}"
            time.sleep(0.2)
        record["target_exit_before_cleanup"] = proc.poll()
        record["target_alive_before_cleanup"] = proc.poll() is None
        record["health_response_first_line"] = None
        if proc.poll() is None:
            health = send_udp(make_options(f"health{int(time.time())}{repeat}"), 1.0)
            if health is not None:
                record["health_response_first_line"] = health.split(b"\r\n", 1)[0].decode("ascii", "replace")
        record["health_probe_passed"] = bool(record["health_response_first_line"] and record["health_response_first_line"].startswith("SIP/2.0 200"))
        if proc.poll() is None:
            try:
                os.killpg(proc.pid, signal.SIGTERM)
                record["target_exit_after_cleanup"] = proc.wait(timeout=5.0)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                record["target_exit_after_cleanup"] = proc.wait(timeout=2.0)
        else:
            record["target_exit_after_cleanup"] = proc.returncode
        record["opensips_log"] = log_path.name
        if record.get("candidate_send_error", "").startswith("candidate exceeds"):
            record["classification"] = "unreplayable_udp_datagram_exceeds_limit"
        elif record["target_exit_before_cleanup"] is not None:
            record["classification"] = "target_exited_before_cleanup"
        elif record["target_alive_before_cleanup"] and record["health_probe_passed"]:
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
    items = sorted(path for path in candidates.iterdir() if path.is_file())
    records = []
    records_path = out_dir / "triage-records.jsonl"
    with records_path.open("w") as stream:
        for candidate in items:
            for n in range(1, repeats + 1):
                record = replay(candidate, out_dir, n)
                records.append(record)
                stream.write(json.dumps(record, sort_keys=True) + "\n")
                stream.flush()
    counts = collections.Counter(record["classification"] for record in records)
    summary = {
        "protocol": "SIP/UDP",
        "implementation": "OpenSIPS 4.0.3",
        "method": "fresh OpenSIPS process per candidate replay; follow with a valid SIP OPTIONS health check",
        "repetitions_per_candidate": repeats,
        "records": records,
        "classification_counts": dict(counts),
    }
    (out_dir / "triage-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary["classification_counts"], sort_keys=True))


if __name__ == "__main__":
    main()
