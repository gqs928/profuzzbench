#!/usr/bin/env python3
"""Exercise DICOM association, Verification, Storage and release over TCP."""
from __future__ import annotations

import argparse
import json
import socket
import struct
import time
from pathlib import Path

from prepare_seeds import (associate_request, command_pdata, dataset_pdata,
                           make_dataset, make_echo, make_store, pdu)


def recv_exact(sock: socket.socket, size: int) -> bytes:
    chunks = bytearray()
    while len(chunks) < size:
        data = sock.recv(size - len(chunks))
        if not data:
            raise EOFError(f"peer closed after {len(chunks)} of {size} bytes")
        chunks.extend(data)
    return bytes(chunks)


def recv_pdu(sock: socket.socket) -> tuple[int, bytes]:
    header = recv_exact(sock, 6)
    kind, _reserved, size = header[0], header[1], struct.unpack(">I", header[2:])[0]
    if size > 16 * 1024 * 1024:
        raise ValueError(f"server PDU too large: {size}")
    return kind, recv_exact(sock, size)


def command_fields(pdv: bytes) -> dict[tuple[int, int], bytes]:
    fields: dict[tuple[int, int], bytes] = {}
    offset = 0
    while offset < len(pdv):
        if len(pdv) - offset < 8:
            break
        group, element, size = struct.unpack_from("<HHI", pdv, offset)
        offset += 8
        if size > len(pdv) - offset:
            break
        fields[(group, element)] = pdv[offset:offset + size]
        offset += size
    return fields


def parse_pdata_command(body: bytes) -> tuple[int | None, int | None]:
    offset = 0
    while offset < len(body):
        if len(body) - offset < 4:
            return None, None
        item_size = struct.unpack_from(">I", body, offset)[0]
        if item_size < 2 or item_size > len(body) - offset - 4:
            return None, None
        context_id, control = body[offset + 4], body[offset + 5]
        pdv = body[offset + 6:offset + 4 + item_size]
        if control & 1:
            fields = command_fields(pdv)
            command = fields.get((0, 0x0100))
            status = fields.get((0, 0x0900))
            return (struct.unpack("<H", command)[0] if command and len(command) >= 2 else None,
                    struct.unpack("<H", status)[0] if status and len(status) >= 2 else None)
        offset += 4 + item_size
    return None, None


def expect_command(sock: socket.socket, expected: int) -> dict[str, int]:
    deadline = time.monotonic() + 5
    observed: list[int] = []
    while time.monotonic() < deadline:
        kind, body = recv_pdu(sock)
        observed.append(kind)
        if kind != 0x04:
            continue
        command, status = parse_pdata_command(body)
        if command == expected:
            return {"command": command, "status": status if status is not None else -1,
                    "response_pdus": len(observed)}
    raise TimeoutError(f"no DIMSE response 0x{expected:04x}; saw {observed}")


def run_once(host: str, port: int, timeout: float) -> dict[str, object]:
    with socket.create_connection((host, port), timeout=timeout) as sock:
        sock.settimeout(timeout)
        sock.sendall(associate_request())
        kind, body = recv_pdu(sock)
        if kind != 0x02:
            raise RuntimeError(f"association rejected: response PDU type=0x{kind:02x}")
        accepted = {"type": kind, "body_bytes": len(body)}

        sock.sendall(command_pdata(1, make_echo()))
        echo = expect_command(sock, 0x8030)
        if echo["status"] != 0:
            raise RuntimeError(f"C-ECHO status was 0x{echo['status']:04x}")

        sock.sendall(command_pdata(3, make_store()) +
                     dataset_pdata(3, make_dataset()))
        store = expect_command(sock, 0x8001)
        if store["status"] != 0:
            raise RuntimeError(f"C-STORE status was 0x{store['status']:04x}")

        sock.sendall(pdu(0x05, bytes(4)))
        kind, _ = recv_pdu(sock)
        if kind != 0x06:
            raise RuntimeError(f"release response PDU type=0x{kind:02x}")
        return {"association_accept": accepted, "c_echo": echo,
                "c_store": store, "release_response_type": kind}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=11112)
    parser.add_argument("--passes", type=int, default=3)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    records = []
    for _ in range(args.passes):
        records.append(run_once(args.host, args.port, timeout=5.0))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"passes": records}, indent=2) + "\n",
                           encoding="utf-8")
    print(f"PASS: {len(records)} DICOM association/C-ECHO/C-STORE/release flows; {args.output}")


if __name__ == "__main__":
    main()
