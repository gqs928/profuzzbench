#!/usr/bin/env python3
"""Replay AFLNet's saved hang candidates through the TiDB auth proxy."""
import argparse
import json
import pathlib
import socket


def parse_frames(data):
    pos = 0
    while pos + 4 <= len(data):
        size = data[pos] | data[pos + 1] << 8 | data[pos + 2] << 16
        if pos + 4 + size > len(data):
            break
        payload = data[pos + 4 : pos + 4 + size]
        yield data[pos + 3], payload
        pos += 4 + size


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("aflnet_out", type=pathlib.Path)
    parser.add_argument("--port", type=int, default=14001)
    parser.add_argument("--idle-timeout", type=float, default=0.35)
    args = parser.parse_args()

    candidates = sorted((args.aflnet_out / "replayable-hangs").glob("id:*"))
    if not candidates:
        raise SystemExit("no saved replayable-hangs candidates")

    report = {
        "candidate_count": len(candidates),
        "proxy": f"127.0.0.1:{args.port}",
        "idle_timeout_seconds": args.idle_timeout,
        "samples": [],
    }
    for path in candidates:
        received = bytearray()
        sample = {
            "file": path.name,
            "request_bytes": path.stat().st_size,
            "received_bytes": 0,
            "response_packets": 0,
            "response_markers": [],
            "connect_error": None,
            "send_error": None,
            "receive_error": None,
            "peer_closed": False,
            "idle_read_timeout": False,
        }
        try:
            sock = socket.create_connection(("127.0.0.1", args.port), timeout=5)
        except OSError as exc:
            sample["connect_error"] = f"{type(exc).__name__}: {exc}"
        else:
            try:
                sock.settimeout(args.idle_timeout)
                try:
                    sock.sendall(path.read_bytes())
                except OSError as exc:
                    sample["send_error"] = f"{type(exc).__name__}: {exc}"
                else:
                    while True:
                        try:
                            chunk = sock.recv(65536)
                        except socket.timeout:
                            sample["idle_read_timeout"] = True
                            break
                        except OSError as exc:
                            sample["receive_error"] = f"{type(exc).__name__}: {exc}"
                            break
                        if not chunk:
                            sample["peer_closed"] = True
                            break
                        received.extend(chunk)
            finally:
                sock.close()

        frames = list(parse_frames(received))
        sample["received_bytes"] = len(received)
        sample["response_packets"] = len(frames)
        sample["response_markers"] = [payload[0] for _, payload in frames if payload]
        if sample["connect_error"]:
            sample["outcome"] = "connect_error"
        elif sample["send_error"]:
            sample["outcome"] = "send_error"
        elif sample["receive_error"]:
            sample["outcome"] = "receive_error"
        elif sample["peer_closed"]:
            sample["outcome"] = "peer_close_after_response" if received else "peer_close_without_response"
        elif sample["idle_read_timeout"]:
            sample["outcome"] = "response_then_idle_timeout" if received else "idle_timeout_without_response"
        else:
            sample["outcome"] = "unknown"
        report["samples"].append(sample)

    (args.aflnet_out / "hang-triage.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
