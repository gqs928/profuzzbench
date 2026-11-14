#!/usr/bin/env python3
"""Exercise two MQTT versions against clean reference and AFL/ASan brokers."""

from __future__ import annotations

import hashlib
import json
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

from mqtt_packets import connect, decode_packet, publish, recv_packet, subscribe, unsubscribe


PORT = 1883
CONFIG = os.environ.get("MOSQUITTO_CONFIG", "/workspace/mosquitto.conf")
REPETITIONS = int(os.environ.get("MQTT_SMOKE_REPETITIONS", "10"))


class SmokeFailure(RuntimeError):
    pass


def exchange(sock: socket.socket, sent: bytes) -> bytes:
    sock.sendall(sent)
    return recv_packet(sock)


def exercise_connection(sock: socket.socket, level: int) -> list[dict[str, str]]:
    transcript: list[dict[str, str]] = []

    def record(direction: str, data: bytes) -> None:
        transcript.append({"direction": direction, "hex": data.hex()})

    connack = exchange(sock, connect(level, f"mqtt-bench-{level}"))
    record("client", connect(level, f"mqtt-bench-{level}"))
    record("server", connack)
    packet_type, _, body = decode_packet(connack)
    if packet_type != 2 or len(body) < 2 or body[1] != 0:
        raise SmokeFailure(f"MQTT {level}: unsuccessful CONNACK: {connack.hex()}")

    sub = subscribe(level)
    suback = exchange(sock, sub)
    record("client", sub)
    record("server", suback)
    packet_type, _, body = decode_packet(suback)
    expected_suback = b"\x00\x01\x00" if level == 4 else b"\x00\x01\x00\x00"
    if packet_type != 9 or body != expected_suback:
        raise SmokeFailure(f"MQTT {level}: unexpected SUBACK: {suback.hex()}")

    pub = publish(level)
    echoed = exchange(sock, pub)
    record("client", pub)
    record("server", echoed)
    packet_type, _, body = decode_packet(echoed)
    if packet_type != 3:
        raise SmokeFailure(f"MQTT {level}: expected forwarded PUBLISH, got {echoed.hex()}")
    topic_length = int.from_bytes(body[:2], "big")
    offset = 2 + topic_length
    if body[2:offset] != b"bench/topic":
        raise SmokeFailure(f"MQTT {level}: wrong forwarded topic: {echoed.hex()}")
    if level == 5:
        if offset >= len(body) or body[offset] != 0:
            raise SmokeFailure(f"MQTT 5.0: unexpected PUBLISH properties: {echoed.hex()}")
        offset += 1
    if body[offset:] != b"baseline-payload":
        raise SmokeFailure(f"MQTT {level}: wrong forwarded payload: {echoed.hex()}")

    unsub = unsubscribe(level)
    unsuback = exchange(sock, unsub)
    record("client", unsub)
    record("server", unsuback)
    packet_type, _, body = decode_packet(unsuback)
    expected_unsuback = b"\x00\x02" if level == 4 else b"\x00\x02\x00\x00"
    if packet_type != 11 or body != expected_unsuback:
        raise SmokeFailure(f"MQTT {level}: unexpected UNSUBACK: {unsuback.hex()}")

    pingresp = exchange(sock, b"\xc0\x00")
    record("client", b"\xc0\x00")
    record("server", pingresp)
    if pingresp != b"\xd0\x00":
        raise SmokeFailure(f"MQTT {level}: unexpected PINGRESP: {pingresp.hex()}")

    disconnect = b"\xe0\x00"
    sock.sendall(disconnect)
    record("client", disconnect)
    return transcript


def run_one(build: str, binary: Path, level: int, repetition: int,
            output_dir: Path) -> str:
    tag = f"{build}-v{level}-run{repetition:02d}"
    log_path = output_dir / f"{tag}.log"
    transcript_path = output_dir / f"{tag}.json"
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = str(binary.parent.parent / "lib")
    with log_path.open("wb") as log:
        proc = subprocess.Popen(
            [str(binary), "-c", CONFIG],
            stdout=log,
            stderr=subprocess.STDOUT,
            env=env,
            start_new_session=True,
        )
        sock: socket.socket | None = None
        try:
            deadline = time.monotonic() + 10
            while True:
                if proc.poll() is not None:
                    raise SmokeFailure(f"{tag}: broker exited {proc.returncode}; see {log_path}")
                try:
                    probe = socket.create_connection(("127.0.0.1", PORT), timeout=0.2)
                    probe.close()
                    break
                except OSError:
                    if time.monotonic() >= deadline:
                        raise SmokeFailure(f"{tag}: broker did not listen on {PORT}; see {log_path}")
                    time.sleep(0.05)

            sock = socket.create_connection(("127.0.0.1", PORT), timeout=3)
            sock.settimeout(3)
            transcript = exercise_connection(sock, level)
            encoded = json.dumps(transcript, indent=2) + "\n"
            transcript_path.write_text(encoded, encoding="utf-8")
            return hashlib.sha256(encoded.encode("utf-8")).hexdigest()
        finally:
            if sock is not None:
                sock.close()
            if proc.poll() is None:
                proc.send_signal(signal.SIGTERM)
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=5)
            log.flush()
            log_data = log_path.read_bytes()
            if proc.returncode != 0:
                raise SmokeFailure(f"{tag}: broker shutdown returned {proc.returncode}; see {log_path}")
            if b"AddressSanitizer:" in log_data or b"runtime error:" in log_data:
                raise SmokeFailure(f"{tag}: sanitizer report found; see {log_path}")


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: protocol_smoke.py OUTPUT_DIR", file=sys.stderr)
        return 2
    output_dir = Path(sys.argv[1])
    output_dir.mkdir(parents=True, exist_ok=True)
    builds = {
        "reference": Path(os.environ.get("MOSQUITTO_REFERENCE_BIN", "")),
        "afl": Path(os.environ.get("MOSQUITTO_AFL_BIN", "")),
    }
    for name, path in builds.items():
        if not path.is_file():
            raise SystemExit(f"{name} broker binary missing: {path}")
    if not 1 <= REPETITIONS <= 100:
        raise SystemExit("MQTT_SMOKE_REPETITIONS must be between 1 and 100")

    results: dict[str, dict[str, list[str]]] = {}
    for build, binary in builds.items():
        results[build] = {}
        for level in (4, 5):
            hashes = [
                run_one(build, binary, level, index + 1, output_dir)
                for index in range(REPETITIONS)
            ]
            if len(set(hashes)) != 1:
                raise SmokeFailure(
                    f"{build} MQTT {level} responses varied across fresh broker runs: {hashes}"
                )
            results[build][f"mqtt_{level}"] = hashes

    for level in (4, 5):
        reference = results["reference"][f"mqtt_{level}"][0]
        instrumented = results["afl"][f"mqtt_{level}"][0]
        if reference != instrumented:
            raise SmokeFailure(
                f"MQTT {level} reference/AFL transcript hash mismatch: "
                f"{reference} != {instrumented}"
            )

    summary = {
        "repetitions_per_build_and_version": REPETITIONS,
        "versions": {"mqtt_4": "3.1.1", "mqtt_5": "5.0"},
        "transcript_hashes": results,
        "transcripts_and_logs": str(output_dir),
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(
        "PASS: MQTT 3.1.1 and 5.0 CONNECT/SUBSCRIBE/PUBLISH/UNSUBSCRIBE/"
        f"PING/DISCONNECT; {REPETITIONS} fresh brokers per build/version."
    )
    print(f"Reference and ASan-instrumented transcript hashes match; evidence={output_dir}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, EOFError, TimeoutError, ValueError, SmokeFailure) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
