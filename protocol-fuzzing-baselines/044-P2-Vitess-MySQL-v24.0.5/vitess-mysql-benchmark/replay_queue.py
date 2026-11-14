#!/usr/bin/env python3
"""Replay AFLNet MySQL Classic queue cases through the auth proxy."""
import json
import pathlib
import socket
import sys
import time


def frames(data):
    pos = 0
    while pos + 4 <= len(data):
        size = data[pos] | data[pos + 1] << 8 | data[pos + 2] << 16
        if pos + 4 + size > len(data):
            break
        yield data[pos + 3], data[pos + 4 : pos + 4 + size]
        pos += 4 + size


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: replay_queue.py AFLNET_OUT PROXY_PORT")
    root = pathlib.Path(sys.argv[1])
    port = int(sys.argv[2])
    files = sorted(p for p in root.glob("**/queue/id:*") if p.is_file())
    out = {
        "queue_files": len(files),
        "connected": 0,
        "connect_errors": 0,
        "send_errors": 0,
        "receive_errors": 0,
        "connection_errors": 0,
        "timeouts": 0,
        "peer_closes": 0,
        "response_bytes": 0,
        "response_packets": 0,
        "ok_packets": 0,
        "error_packets": 0,
        "eof_packets": 0,
        "result_header_packets": 0,
        "read_idle_timeout_seconds": 0.35,
        "per_testcase_read_window_seconds": 1.5,
        "samples": [],
    }

    for path in files:
        data = bytearray()
        sample = {
            "file": path.name,
            "connected": False,
            "bytes_received": 0,
            "response_packets": 0,
            "error_packets": 0,
            "eof_packets": 0,
            "connect_error": None,
            "send_error": None,
            "receive_error": None,
            "idle_read_timeout": False,
            "peer_closed": False,
        }
        try:
            sock = socket.create_connection(("127.0.0.1", port), timeout=5)
        except OSError as exc:
            out["connect_errors"] += 1
            out["connection_errors"] += 1
            sample["connect_error"] = f"{type(exc).__name__}: {exc}"
        else:
            out["connected"] += 1
            sample["connected"] = True
            try:
                sock.settimeout(out["read_idle_timeout_seconds"])
                try:
                    sock.sendall(path.read_bytes())
                except OSError as exc:
                    out["send_errors"] += 1
                    out["connection_errors"] += 1
                    sample["send_error"] = f"{type(exc).__name__}: {exc}"
                else:
                    deadline = time.monotonic() + out["per_testcase_read_window_seconds"]
                    while time.monotonic() < deadline:
                        try:
                            chunk = sock.recv(65536)
                        except socket.timeout:
                            out["timeouts"] += 1
                            sample["idle_read_timeout"] = True
                            break
                        except OSError as exc:
                            out["receive_errors"] += 1
                            out["connection_errors"] += 1
                            sample["receive_error"] = f"{type(exc).__name__}: {exc}"
                            break
                        if not chunk:
                            out["peer_closes"] += 1
                            sample["peer_closed"] = True
                            break
                        data.extend(chunk)
            finally:
                sock.close()

        parsed = list(frames(data))
        markers = [payload[0] for _, payload in parsed if payload]
        sample["bytes_received"] = len(data)
        sample["response_packets"] = len(parsed)
        sample["error_packets"] = markers.count(0xFF)
        sample["eof_packets"] = markers.count(0xFE)
        out["response_bytes"] += len(data)
        out["response_packets"] += len(parsed)
        out["ok_packets"] += markers.count(0x00)
        out["error_packets"] += markers.count(0xFF)
        out["eof_packets"] += markers.count(0xFE)
        out["result_header_packets"] += sum(1 for marker in markers if 0 < marker < 0xFB)
        out["samples"].append(sample)

    (root / "queue-replay.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in out.items() if key != "samples"}, indent=2))


if __name__ == "__main__":
    main()
