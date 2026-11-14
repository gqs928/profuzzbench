#!/usr/bin/env python3
"""Small RTMP v3 handshake, AMF0 command, and chunk helpers for this profile."""
from __future__ import annotations
import random
import struct


def amf_string(value: str) -> bytes:
    raw = value.encode()
    return b"\x02" + struct.pack(">H", len(raw)) + raw


def amf_number(value: float) -> bytes:
    return b"\x00" + struct.pack(">d", value)


def amf_boolean(value: bool) -> bytes:
    return b"\x01" + bytes([1 if value else 0])


def amf_null() -> bytes:
    return b"\x05"


def amf_object(values: list[tuple[str, bytes]]) -> bytes:
    out = bytearray(b"\x03")
    for key, value in values:
        raw = key.encode()
        out.extend(struct.pack(">H", len(raw)))
        out.extend(raw)
        out.extend(value)
    out.extend(b"\x00\x00\x09")
    return bytes(out)


def connect_command(host: str = "127.0.0.1", port: int = 1935) -> bytes:
    props = [
        ("app", amf_string("live")),
        ("type", amf_string("nonprivate")),
        ("tcUrl", amf_string(f"rtmp://{host}:{port}/live")),
        ("flashVer", amf_string("FMLE/3.0 (compatible; FMSc/1.0)")),
        ("fpad", amf_boolean(False)),
        ("capabilities", amf_number(15)),
        ("audioCodecs", amf_number(4071)),
        ("videoCodecs", amf_number(252)),
        ("videoFunction", amf_number(1)),
        ("objectEncoding", amf_number(0)),
    ]
    return amf_string("connect") + amf_number(1) + amf_object(props)


def command(name: str, transaction_id: float, *arguments: bytes) -> bytes:
    return amf_string(name) + amf_number(transaction_id) + b"".join(arguments)


def rtmp_message(payload: bytes, message_type: int = 20,
                 stream_id: int = 0, chunk_size: int = 128,
                 chunk_stream_id: int = 3) -> bytes:
    if len(payload) > 0xFFFFFF:
        raise ValueError("RTMP message body exceeds the 24-bit message length")
    first = (
        bytes([chunk_stream_id & 0x3F])
        + b"\x00\x00\x00"
        + len(payload).to_bytes(3, "big")
        + bytes([message_type])
        + struct.pack("<I", stream_id)
    )
    out = bytearray(first)
    out.extend(payload[:chunk_size])
    offset = chunk_size
    while offset < len(payload):
        out.append(0xC0 | (chunk_stream_id & 0x3F))
        take = min(chunk_size, len(payload) - offset)
        out.extend(payload[offset:offset + take])
        offset += take
    return bytes(out)


def handshake_seed() -> bytes:
    rng = random.Random(0x4D545850)
    c1 = struct.pack(">II", 1, 0) + bytes(rng.randrange(256) for _ in range(1528))
    return b"\x03" + c1 + (b"\x00" * 1536)


def corpus() -> dict[str, bytes]:
    prefix = handshake_seed()
    connect = rtmp_message(connect_command())
    create = rtmp_message(command("createStream", 2, amf_null()))
    release = rtmp_message(command("releaseStream", 3, amf_null(), amf_string("bench")))
    publish = rtmp_message(command(
        "publish", 4, amf_null(), amf_string("bench"), amf_string("live")
    ), stream_id=1)
    return {
        "connect": prefix + connect,
        "connect-create-stream": prefix + connect + create,
        "connect-release-publish": prefix + connect + release + publish,
    }


if __name__ == "__main__":
    import argparse
    from pathlib import Path
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    args.directory.mkdir(parents=True, exist_ok=True)
    for name, data in corpus().items():
        (args.directory / name).write_bytes(data)
    print(f"generated={len(corpus())} protocol=RTMP v3 over TCP")
