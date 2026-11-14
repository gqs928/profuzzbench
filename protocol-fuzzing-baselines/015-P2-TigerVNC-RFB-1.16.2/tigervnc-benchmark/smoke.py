#!/usr/bin/env python3
import argparse
import json
import socket
import struct
import time
from pathlib import Path


def read_exact(sock: socket.socket, size: int) -> bytes:
    data = bytearray()
    while len(data) < size:
        part = sock.recv(size - len(data))
        if not part:
            raise RuntimeError(f"connection closed after {len(data)} of {size} bytes")
        data.extend(part)
    return bytes(data)


def transact(timeout: float) -> dict:
    deadline = time.monotonic() + timeout
    last_error = None
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", 5901), timeout=2) as sock:
                sock.settimeout(3)
                banner = read_exact(sock, 12)
                if not banner.startswith(b"RFB ") or not banner.endswith(b"\n"):
                    raise RuntimeError(f"invalid RFB banner: {banner!r}")
                sock.sendall(b"RFB 003.008\n")
                count = read_exact(sock, 1)[0]
                if count == 0 or count > 32:
                    raise RuntimeError(f"invalid RFB security type count: {count}")
                security_types = read_exact(sock, count)
                if 1 not in security_types:
                    raise RuntimeError(f"RFB None security type unavailable: {security_types!r}")
                sock.sendall(b"\x01")
                result = struct.unpack("!I", read_exact(sock, 4))[0]
                if result != 0:
                    raise RuntimeError(f"RFB None security failed with result {result}")
                sock.sendall(b"\x01")
                header = read_exact(sock, 24)
                width, height = struct.unpack("!HH", header[:4])
                name_len = struct.unpack("!I", header[20:24])[0]
                if width == 0 or height == 0 or name_len > 65536:
                    raise RuntimeError(f"invalid RFB ServerInit: {width}x{height}, name={name_len}")
                name = read_exact(sock, name_len)
                sock.sendall(bytes([3, 0]) + struct.pack("!HHHH", 0, 0, width, height))
                return {
                    "status": "pass",
                    "server_banner": banner.decode("ascii", "replace").strip(),
                    "security_types": list(security_types),
                    "framebuffer": {"width": width, "height": height},
                    "desktop_name": name.decode("utf-8", "replace"),
                    "framebuffer_update_request_sent": True,
                }
        except (OSError, RuntimeError) as exc:
            last_error = str(exc)
            time.sleep(0.25)
    raise RuntimeError(last_error or "RFB smoke timeout")


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
