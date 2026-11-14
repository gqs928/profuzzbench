"""Small deterministic MQTT 3.1.1/5.0 wire helpers for seeds and smoke tests."""

from __future__ import annotations


def encode_remaining_length(value: int) -> bytes:
    if not 0 <= value <= 268_435_455:
        raise ValueError("MQTT Remaining Length out of range")
    encoded = bytearray()
    while True:
        digit = value % 128
        value //= 128
        if value:
            digit |= 0x80
        encoded.append(digit)
        if not value:
            return bytes(encoded)


def packet(first_byte: int, body: bytes) -> bytes:
    return bytes((first_byte,)) + encode_remaining_length(len(body)) + body


def utf8(value: str) -> bytes:
    encoded = value.encode("utf-8")
    if len(encoded) > 65535:
        raise ValueError("MQTT UTF-8 field too long")
    return len(encoded).to_bytes(2, "big") + encoded


def connect(level: int = 4, client_id: str = "mqtt-bench") -> bytes:
    if level not in (4, 5):
        raise ValueError("only MQTT 3.1.1 (4) and MQTT 5.0 (5) are supported")
    body = utf8("MQTT") + bytes((level, 0x02)) + (30).to_bytes(2, "big")
    if level == 5:
        body += b"\x00"  # zero-length CONNECT properties
    body += utf8(client_id)
    return packet(0x10, body)


def subscribe(level: int = 4, packet_id: int = 1,
              topic: str = "bench/topic") -> bytes:
    body = packet_id.to_bytes(2, "big")
    if level == 5:
        body += b"\x00"  # zero-length SUBSCRIBE properties
    body += utf8(topic) + b"\x00"
    return packet(0x82, body)


def publish(level: int = 4, topic: str = "bench/topic",
            payload: bytes = b"baseline-payload") -> bytes:
    body = utf8(topic)
    if level == 5:
        body += b"\x00"  # zero-length PUBLISH properties
    return packet(0x30, body + payload)


def unsubscribe(level: int = 4, packet_id: int = 2,
                topic: str = "bench/topic") -> bytes:
    body = packet_id.to_bytes(2, "big")
    if level == 5:
        body += b"\x00"  # zero-length UNSUBSCRIBE properties
    body += utf8(topic)
    return packet(0xA2, body)


def business_session(level: int = 4, client_id: str = "mqtt-bench") -> bytes:
    return (
        connect(level, client_id)
        + subscribe(level)
        + publish(level)
        + unsubscribe(level)
        + b"\xc0\x00"  # PINGREQ
        + b"\xe0\x00"  # DISCONNECT
    )


def decode_packet(data: bytes) -> tuple[int, int, bytes]:
    """Decode one complete packet, returning type, body offset, and body."""
    if len(data) < 2:
        raise ValueError("short MQTT packet")
    value = 0
    multiplier = 1
    for index in range(1, min(len(data), 5)):
        digit = data[index]
        value += (digit & 0x7F) * multiplier
        if not digit & 0x80:
            body_offset = index + 1
            if len(data) != body_offset + value:
                raise ValueError("MQTT packet length mismatch")
            return (data[0] >> 4) & 0x0F, body_offset, data[body_offset:]
        multiplier *= 128
    raise ValueError("invalid or incomplete MQTT Remaining Length")


def recv_packet(sock) -> bytes:
    """Read exactly one MQTT packet from a socket without over-reading."""
    first = _recv_exact(sock, 1)
    length = bytearray()
    for _ in range(4):
        digit = _recv_exact(sock, 1)
        length += digit
        if digit[0] < 0x80:
            break
    else:
        raise ValueError("server sent an invalid Remaining Length")
    value = 0
    multiplier = 1
    for digit in length:
        value += (digit & 0x7F) * multiplier
        multiplier *= 128
    return first + bytes(length) + _recv_exact(sock, value)


def _recv_exact(sock, count: int) -> bytes:
    output = bytearray()
    while len(output) < count:
        chunk = sock.recv(count - len(output))
        if not chunk:
            raise EOFError(f"connection closed with {count - len(output)} bytes outstanding")
        output += chunk
    return bytes(output)
