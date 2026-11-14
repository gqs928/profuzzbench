#!/usr/bin/env python3
"""Exercise MQTT 3.1.1 and 5.0 publish/subscribe on a NanoMQ broker."""

from __future__ import annotations

import hashlib
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

from mqtt_packets import connect, publish, subscribe, unsubscribe
from wait_mqtt import wait_for_mqtt


def recv_exact(sock: socket.socket, size: int) -> bytes:
    data = bytearray()
    while len(data) < size:
        chunk = sock.recv(size - len(data))
        if not chunk:
            raise EOFError(f"connection closed with {size - len(data)} bytes outstanding")
        data.extend(chunk)
    return bytes(data)


def recv_packet(sock: socket.socket) -> bytes:
    header = bytearray(recv_exact(sock, 1))
    length = bytearray()
    for _ in range(4):
        digit = recv_exact(sock, 1)
        length.extend(digit)
        if digit[0] < 0x80:
            break
    else:
        raise ValueError("invalid Remaining Length from broker")
    remaining = 0
    multiplier = 1
    for digit in length:
        remaining += (digit & 0x7F) * multiplier
        multiplier *= 128
    return bytes(header + length) + recv_exact(sock, remaining)


def open_client(client_id: str, level: int) -> tuple[socket.socket, list[bytes]]:
    sock = socket.create_connection(("127.0.0.1", 1883), timeout=3)
    sock.settimeout(3)
    sock.sendall(connect(level, client_id))
    connack = recv_packet(sock)
    if (connack[0] >> 4) != 2 or len(connack) < 4 or connack[3] != 0:
        raise AssertionError(f"CONNECT failed: {connack.hex()}")
    return sock, [connack]


def run_flow(level: int, repeat: int) -> dict[str, object]:
    topic = f"baseline/nanomq/{level}/{repeat}"
    client_id = f"nanomq-bench-{level}-{repeat}"
    subscriber, sub_transcript = open_client(client_id + "-sub", level)
    publisher, pub_transcript = open_client(client_id + "-pub", level)
    try:
        subscriber.sendall(subscribe(level, 1, topic))
        suback = recv_packet(subscriber)
        if (suback[0] >> 4) != 9:
            raise AssertionError(f"SUBSCRIBE did not receive SUBACK: {suback.hex()}")
        sub_transcript.append(suback)

        publisher.sendall(publish(level, topic, b"nanomq-baseline-payload"))
        forwarded = recv_packet(subscriber)
        if (forwarded[0] >> 4) != 3:
            raise AssertionError(f"subscriber did not receive PUBLISH: {forwarded.hex()}")

        subscriber.sendall(b"\xc0\x00")
        pingresp = recv_packet(subscriber)
        if pingresp != b"\xd0\x00":
            raise AssertionError(f"PINGREQ did not receive PINGRESP: {pingresp.hex()}")
        sub_transcript.append(pingresp)

        subscriber.sendall(unsubscribe(level, 2, topic))
        unsuback = recv_packet(subscriber)
        if (unsuback[0] >> 4) != 11:
            raise AssertionError(f"UNSUBSCRIBE did not receive UNSUBACK: {unsuback.hex()}")
        sub_transcript.append(unsuback)

        publisher.sendall(b"\xe0\x00")
        subscriber.sendall(b"\xe0\x00")
        return {
            "protocol_level": level,
            "repeat": repeat,
            "client_ids": [client_id + "-sub", client_id + "-pub"],
            "subscriber_responses_sha256": hashlib.sha256(b"".join(sub_transcript)).hexdigest(),
            "publisher_responses_sha256": hashlib.sha256(b"".join(pub_transcript)).hexdigest(),
            "forwarded_publish_sha256": hashlib.sha256(forwarded).hexdigest(),
            "response_types": [2, 9, 3, 13, 11],
            "status": "pass",
        }
    finally:
        subscriber.close()
        publisher.close()


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: service_smoke.py OUTPUT_DIR", file=sys.stderr)
        return 2
    output = Path(sys.argv[1])
    output.mkdir(parents=True, exist_ok=False)
    with (output / "nanomq.log").open("wb") as log:
        broker = subprocess.Popen(
            ["/opt/nanomq/nanomq", "start", "--conf", "/work/nanomq.conf"],
            cwd="/work",
            stdout=log,
            stderr=subprocess.STDOUT,
        )
        try:
            try:
                wait_for_mqtt(timeout=120)
            except TimeoutError as exc:
                if broker.poll() is not None:
                    raise RuntimeError(f"NanoMQ exited early with {broker.returncode}") from exc
                raise

            started = time.time()
            flows = [run_flow(level, repeat) for level in (4, 5) for repeat in range(1, 4)]
            (output / "service-smoke.json").write_text(
                json.dumps(
                    {"flows": flows, "elapsed_seconds": time.time() - started, "broker_pid": broker.pid},
                    indent=2,
                ) + "\n"
            )
            print(f"PASS: {len(flows)} MQTT 3.1.1/5.0 publish-subscribe flows")
        finally:
            if broker.poll() is None:
                broker.terminate()
                try:
                    broker.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    broker.kill()
                    broker.wait()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
