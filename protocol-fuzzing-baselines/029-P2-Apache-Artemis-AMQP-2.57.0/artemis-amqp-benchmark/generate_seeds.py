#!/usr/bin/env python3
"""Generate compact AMQP 1.0 TCP/SASL seeds with explicit frame boundaries."""
from pathlib import Path
import struct

OUT = Path(__file__).with_name("seeds")
SASL_HEADER = b"AMQP\x03\x01\x00\x00"
AMQP_HEADER = b"AMQP\x00\x01\x00\x00"


def symbol(text: str) -> bytes:
    raw = text.encode()
    return b"\xa3" + bytes([len(raw)]) + raw


def string(text: str) -> bytes:
    raw = text.encode()
    return b"\xa1" + bytes([len(raw)]) + raw


def binary(raw: bytes) -> bytes:
    return b"\xa0" + bytes([len(raw)]) + raw


def list8(items: list[bytes]) -> bytes:
    body = b"".join(items)
    return b"\xc0" + bytes([len(body) + 1, len(items)]) + body


def performative(code: int, items: list[bytes]) -> bytes:
    return b"\x00\x53" + bytes([code]) + list8(items)


def frame(body: bytes, frame_type: int = 0, channel: int = 0) -> bytes:
    size = 8 + len(body)
    return struct.pack("!IBBH", size, 2, frame_type, channel) + body


def sasl_init(user: str = "guest", password: str = "guest") -> bytes:
    response = b"\x00" + user.encode() + b"\x00" + password.encode()
    body = performative(0x41, [symbol("PLAIN"), binary(response)])
    return frame(body, frame_type=1)


def open_frame(container: str = "codex-amqp") -> bytes:
    return frame(performative(0x10, [string(container), string("localhost")]))


def begin_frame() -> bytes:
    return frame(performative(0x11, [b"\x40", b"\x70\x00\x00\x00\x00",
                                    b"\x70\x00\x00\x03\xe8",
                                    b"\x70\x00\x00\x03\xe8"]))


def close_frame() -> bytes:
    return frame(performative(0x18, []))


def write(name: str, data: bytes) -> None:
    (OUT / name).write_bytes(data)


def main() -> None:
    OUT.mkdir(exist_ok=True)
    session = SASL_HEADER + sasl_init() + AMQP_HEADER + open_frame() + begin_frame()
    write("01-sasl-open-begin.amqp", session + close_frame())
    write("02-no-sasl-open-close.amqp", AMQP_HEADER + open_frame("anonymous") + close_frame())
    write("03-sasl-only.amqp", SASL_HEADER + sasl_init())
    write("04-truncated-frame.amqp", AMQP_HEADER + b"\x00\x00\x00\x08\x02\x00")
    write("05-invalid-performative.amqp", AMQP_HEADER + frame(b"\x00\x53\xff\xc0\x01\x00"))
    write("06-open-with-malformed-tail.amqp", SASL_HEADER + sasl_init() + AMQP_HEADER +
          open_frame("mutated") + b"\x00\x00\x00")


if __name__ == "__main__":
    main()
