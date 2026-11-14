#!/usr/bin/env python3
import argparse
import json
import socket
import time
from pathlib import Path


def read_response(sock: socket.socket, timeout: float) -> bytes:
    sock.settimeout(timeout)
    data = bytearray()
    while b"\r\n\r\n" not in data:
        chunk = sock.recv(4096)
        if not chunk:
            break
        data.extend(chunk)
        if len(data) > 1024 * 1024:
            raise RuntimeError("RTSP response exceeded 1 MiB")
    if not data:
        raise RuntimeError("empty RTSP response")
    return bytes(data)


def transact(timeout: float) -> dict:
    deadline = time.monotonic() + timeout
    last_error = None
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", 8554), timeout=2) as sock:
                sock.settimeout(3)
                sock.sendall(b"OPTIONS rtsp://127.0.0.1/live/test RTSP/1.0\r\nCSeq: 1\r\nUser-Agent: profuzzbench\r\n\r\n")
                options = read_response(sock, 3)
                if not options.startswith(b"RTSP/1.0 200"):
                    raise RuntimeError(f"OPTIONS failed: {options[:160]!r}")
                sock.sendall(b"PLAY rtsp://127.0.0.1/live/test RTSP/1.0\r\nCSeq: 2\r\n\r\n")
                play = read_response(sock, 3)
                first_line = play.split(b"\r\n",1)[0].decode("ascii", "replace")
                if first_line != "RTSP/1.0 454 Session Not Found":
                    raise RuntimeError(f"unexpected PLAY response: {first_line!r}")
                return {
                    "status": "pass",
                    "port": 8554,
                    "options_status": 200,
                    "play_status": 454,
                    "options_response": options.split(b"\r\n",1)[0].decode("ascii", "replace"),
                    "play_response": first_line,
                }
        except (OSError, RuntimeError, ValueError) as exc:
            last_error = str(exc)
            time.sleep(0.25)
    raise RuntimeError(last_error or "RTSP smoke timeout")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=float, default=20)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = transact(args.timeout)
    except Exception as exc:
        result = {"status": "fail", "error": str(exc)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    if result["status"] != "pass":
        raise SystemExit(1)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
