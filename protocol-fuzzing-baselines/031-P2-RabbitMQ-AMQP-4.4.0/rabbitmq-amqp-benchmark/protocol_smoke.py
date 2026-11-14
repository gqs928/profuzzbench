#!/usr/bin/env python3
"""Check the AMQP 1.0 SASL/PLAIN and connection-open handshake on port 5672."""
import socket
import struct

from generate_seeds import AMQP_HEADER, SASL_HEADER, open_frame, sasl_init


def exact(sock: socket.socket, size: int) -> bytes:
    data = bytearray()
    while len(data) < size:
        part = sock.recv(size - len(data))
        if not part:
            raise RuntimeError(f"connection closed after {len(data)}/{size} bytes")
        data.extend(part)
    return bytes(data)


def read_frame(sock: socket.socket) -> tuple[int, int, bytes]:
    header = exact(sock, 8)
    length = struct.unpack("!I", header[:4])[0]
    if length < 8 or length > 1_000_000:
        raise RuntimeError(f"invalid AMQP frame size: {length}")
    frame = header + exact(sock, length - 8)
    doff, frame_type = frame[4], frame[5]
    body = frame[doff * 4:]
    if len(body) < 3 or body[:2] != b"\x00\x53":
        raise RuntimeError(f"missing described AMQP performative: {body[:12].hex()}")
    return frame_type, body[2], body


def main() -> None:
    with socket.create_connection(("127.0.0.1", 5672), timeout=10) as sock:
        sock.settimeout(10)
        sock.sendall(SASL_HEADER)
        sasl_header = exact(sock, 8)
        if sasl_header != SASL_HEADER:
            raise RuntimeError(f"unexpected SASL protocol header: {sasl_header.hex()}")
        frame_type, code, _ = read_frame(sock)
        if frame_type != 1 or code != 0x40:
            raise RuntimeError(f"expected sasl-mechanisms, got type={frame_type} code={code:#x}")
        sock.sendall(sasl_init("guest", "guest"))
        frame_type, code, body = read_frame(sock)
        if frame_type != 1 or code != 0x44:
            raise RuntimeError(f"expected sasl-outcome, got type={frame_type} code={code:#x}")
        # sasl-outcome is list8([ubyte]); the value is encoded as smalluint
        # (0x50, value), so the success value follows its constructor byte.
        if len(body) < 8 or body[6] != 0x50 or body[7] != 0:
            raise RuntimeError(f"SASL PLAIN login rejected: {body.hex()}")
        sock.sendall(AMQP_HEADER)
        if exact(sock, 8) != AMQP_HEADER:
            raise RuntimeError("AMQP 1.0 protocol header negotiation failed")
        sock.sendall(open_frame("codex-smoke"))
        frame_type, code, _ = read_frame(sock)
        if frame_type != 0 or code != 0x10:
            raise RuntimeError(f"expected connection.open, got type={frame_type} code={code:#x}")
    print("amqp_1_0_sasl_plain=PASS")
    print("amqp_connection_open=PASS")


if __name__ == "__main__":
    main()
