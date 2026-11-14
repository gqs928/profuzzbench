#!/usr/bin/env python3
"""Replay AFLNet raw NATS queue inputs against fresh server processes."""
from __future__ import annotations

import hashlib
import json
import os
import socket
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

from nats_client import Client

MAX_SAMPLE = 16 * 1024 * 1024
SERVER = os.environ.get("NATS_SERVER", "/usr/local/bin/nats-server")
HOST = os.environ.get("NATS_HOST", "127.0.0.1")
PORT = int(os.environ.get("NATS_PORT", "4222"))


def ready(server: subprocess.Popen[bytes], log: object, timeout: float = 8.0) -> None:
    deadline = time.monotonic() + timeout
    last_error = "not attempted"
    while time.monotonic() < deadline:
        if server.poll() is not None:
            raise RuntimeError(f"NATS exited before ready (rc={server.returncode})")
        try:
            client = Client(socket.create_connection((HOST, PORT), timeout=0.25))
            client.sock.settimeout(0.5)
            event = client.event()
            client.sock.close()
            if event["kind"] != "INFO":
                raise RuntimeError(f"expected INFO readiness event; got {event}")
            return
        except (OSError, TimeoutError, ConnectionError, ValueError) as exc:
            last_error = str(exc)
            time.sleep(0.05)
    raise TimeoutError(f"NATS did not become ready: {last_error}")


def stop(server: subprocess.Popen[bytes]) -> int:
    if server.poll() is None:
        server.terminate()
    try:
        return int(server.wait(timeout=3.0))
    except subprocess.TimeoutExpired:
        server.kill()
        return int(server.wait(timeout=3.0))


def replay_one(path: Path, log: object, quiet: float) -> dict[str, object]:
    data = path.read_bytes()
    if len(data) > MAX_SAMPLE:
        return {"sample": path.name, "bytes": len(data), "status": "oversize"}
    server = subprocess.Popen([SERVER, "--addr", HOST, "--port", str(PORT)],
                              stdin=subprocess.DEVNULL, stdout=log, stderr=log)
    started = time.monotonic()
    events: list[dict[str, object]] = []
    error: str | None = None
    status = "ok"
    try:
        ready(server, log)
        client = Client(socket.create_connection((HOST, PORT), timeout=2.0))
        client.sock.settimeout(2.0)
        events.append(client.event())  # Server-first INFO is part of the transcript.
        client.sock.sendall(data)
        quiet_deadline = time.monotonic() + quiet
        while time.monotonic() < quiet_deadline:
            if server.poll() is not None:
                status = "server-exited"
                break
            client.sock.settimeout(max(0.02, quiet_deadline - time.monotonic()))
            try:
                event = client.event()
            except socket.timeout:
                status = "quiet-timeout"
                break
            except (ConnectionError, OSError) as exc:
                status = "peer-closed"
                error = str(exc)
                break
            except (ValueError, OverflowError) as exc:
                status = "response-parse-error"
                error = str(exc)
                break
            events.append(event)
            quiet_deadline = time.monotonic() + quiet
        client.sock.close()
    except (OSError, RuntimeError, TimeoutError, ConnectionError, ValueError) as exc:
        status = "replay-error"
        error = str(exc)
    finally:
        rc = stop(server)
    counts = Counter(str(event.get("kind", "unknown")) for event in events)
    return {"sample": path.name, "sha256": hashlib.sha256(data).hexdigest(),
            "bytes": len(data), "status": status, "error": error,
            "server_exit_code": rc, "response_events": dict(sorted(counts.items())),
            "event_count": len(events), "elapsed_seconds": round(time.monotonic()-started, 4)}


def main() -> int:
    if len(sys.argv) not in (3, 4):
        print("usage: replay_queue.py QUEUE_DIR OUTDIR [MAX_SAMPLES]", file=sys.stderr)
        return 2
    queue_dir, outdir = Path(sys.argv[1]), Path(sys.argv[2])
    max_samples = int(sys.argv[3]) if len(sys.argv) == 4 else 0
    quiet = float(os.environ.get("NATS_REPLAY_QUIET_SECONDS", "0.15"))
    if not queue_dir.is_dir():
        raise FileNotFoundError(queue_dir)
    if outdir.exists() and any(outdir.iterdir()):
        raise RuntimeError(f"output directory must be empty: {outdir}")
    outdir.mkdir(parents=True, exist_ok=True)
    samples = sorted(path for path in queue_dir.iterdir()
                     if path.is_file() and not path.name.startswith("."))
    if max_samples > 0:
        samples = samples[:max_samples]
    records = []
    with (outdir / "nats-replay.log").open("ab") as log:
        for index, path in enumerate(samples, 1):
            record = replay_one(path, log, quiet)
            records.append(record)
            if index % 50 == 0:
                print(f"replayed {index}/{len(samples)}")
    totals = Counter()
    statuses = Counter(record["status"] for record in records)
    for record in records:
        totals.update(record["response_events"])
    summary = {"target": "NATS Server 2.15.3", "protocol": "NATS Core client protocol v1",
               "source_queue": str(queue_dir), "sample_count": len(records),
               "status_counts": dict(sorted(statuses.items())),
               "response_event_counts": dict(sorted(totals.items())),
               "records": records}
    (outdir / "replay-summary.json").write_text(json.dumps(summary, indent=2) + "\n",
                                               encoding="utf-8")
    errors = sum(1 for row in records if row["status"] in ("replay-error", "response-parse-error"))
    print(f"replayed {len(records)} NATS streams; {sum(totals.values())} events; {errors} replay errors")
    return 1 if errors else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, TimeoutError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
