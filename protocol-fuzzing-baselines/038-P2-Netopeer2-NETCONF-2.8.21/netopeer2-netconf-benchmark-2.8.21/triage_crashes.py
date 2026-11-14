#!/usr/bin/env python3
"""Replay health-monitor crash candidates and record whether SSH stays available."""
import json
import pathlib
import socket
import subprocess
import time

ROOT = pathlib.Path("/results/netconf-30m")
CRASH_DIR = ROOT / "replayable-crashes"
PROBE = "/opt/benchmark/netconf-ready-check"
RECOVER = "/opt/benchmark/server-recover.sh"
RECOVERY_LOG_DIR = ROOT / "crash-triage-recovery"


def healthy():
    for attempt in range(3):
        result = subprocess.run(
            [PROBE, "--once"], stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, check=False,
        )
        if result.returncode == 0:
            return True
        if attempt < 2:
            time.sleep(0.2)
    return False


def recover():
    RECOVERY_LOG_DIR.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [RECOVER, str(RECOVERY_LOG_DIR)], stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL, check=False,
    )
    return result.returncode == 0


def send_candidate(path):
    try:
        with socket.create_connection(("127.0.0.1", 1830), timeout=4) as sock:
            sock.settimeout(2)
            sock.sendall(path.read_bytes())
            sock.shutdown(socket.SHUT_WR)
            # Drain briefly so the SSH subsystem processes the complete request.
            deadline = time.monotonic() + 0.5
            while time.monotonic() < deadline:
                try:
                    if not sock.recv(65536):
                        break
                except socket.timeout:
                    break
        return "sent"
    except OSError as exc:
        return type(exc).__name__


def main():
    candidates = sorted(p for p in CRASH_DIR.glob("id:*") if p.is_file())
    report = {
        "candidate_count": len(candidates),
        "trials_per_candidate": 3,
        "total_trials": 0,
        "connect_failures": 0,
        "post_test_unavailable": 0,
        "recoveries": 0,
        "recovery_failures": 0,
        "candidates": [],
    }
    for path in candidates:
        item = {"candidate": path.name, "bytes": path.stat().st_size, "trials": []}
        for trial in range(1, 4):
            report["total_trials"] += 1
            if not healthy():
                report["recoveries"] += 1
                if not recover():
                    report["recovery_failures"] += 1
            outcome = send_candidate(path)
            if outcome != "sent":
                report["connect_failures"] += 1
            time.sleep(0.35)
            available = healthy()
            if not available:
                report["post_test_unavailable"] += 1
                report["recoveries"] += 1
                if not recover():
                    report["recovery_failures"] += 1
            item["trials"].append({
                "trial": trial,
                "send": outcome,
                "ssh_available_after_test": available,
            })
        item["outage_reproduced"] = any(
            not trial["ssh_available_after_test"] for trial in item["trials"]
        )
        report["candidates"].append(item)
        (ROOT / "crash-triage.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    report["unconfirmed_candidates"] = sum(
        not item["outage_reproduced"] for item in report["candidates"]
    )
    report["reproduced_candidates"] = sum(
        item["outage_reproduced"] for item in report["candidates"]
    )
    (ROOT / "crash-triage.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({k: v for k, v in report.items() if k != "candidates"}, indent=2))


if __name__ == "__main__":
    main()
