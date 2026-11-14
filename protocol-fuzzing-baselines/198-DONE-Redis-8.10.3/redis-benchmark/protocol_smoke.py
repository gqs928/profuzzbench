#!/usr/bin/env python3
"""Exercise deterministic RESP2/RESP3 command paths on fresh Redis servers."""

from __future__ import annotations

import hashlib
import json
import os
import signal
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path


PORT = 6379
REPETITIONS = int(os.environ.get("REDIS_SMOKE_REPETITIONS", "10"))


class SmokeFailure(RuntimeError):
    pass


class RESPReader:
    def __init__(self, sock: socket.socket):
        self.sock = sock
        self.buffer = bytearray()

    def exact(self, count: int) -> bytes:
        while len(self.buffer) < count:
            data = self.sock.recv(max(4096, count - len(self.buffer)))
            if not data:
                raise EOFError("server closed the connection mid-frame")
            self.buffer.extend(data)
        result = bytes(self.buffer[:count])
        del self.buffer[:count]
        return result

    def line(self) -> bytes:
        while True:
            index = self.buffer.find(b"\r\n")
            if index >= 0:
                result = self.exact(index + 2)
                return result[:-2]
            if len(self.buffer) > 1_048_576:
                raise SmokeFailure("RESP line exceeded 1 MiB")
            data = self.sock.recv(4096)
            if not data:
                raise EOFError("server closed the connection mid-line")
            self.buffer.extend(data)

    def frame(self, first: bytes | None = None) -> bytes:
        marker = self.exact(1) if first is None else first
        if marker in (b"+", b"-", b":", b",", b"(", b"#", b"_"):
            line = self.line()
            if marker == b"_" and line:
                raise SmokeFailure("invalid RESP3 null")
            return marker + line + b"\r\n"
        if marker in (b"$", b"!", b"="):
            line = self.line()
            if line == b"?":
                if marker != b"$":
                    raise SmokeFailure("unexpected streamed blob type")
                chunks = bytearray(marker + b"?\r\n")
                while True:
                    if self.exact(1) != b";":
                        raise SmokeFailure("invalid streamed blob chunk")
                    length_line = self.line()
                    chunks.extend(b";" + length_line + b"\r\n")
                    length = int(length_line)
                    if length == 0:
                        return bytes(chunks)
                    payload = self.exact(length + 2)
                    if not payload.endswith(b"\r\n"):
                        raise SmokeFailure("invalid streamed blob terminator")
                    chunks.extend(payload)
            length = int(line)
            header = marker + line + b"\r\n"
            if length < 0:
                return header
            payload = self.exact(length + 2)
            if not payload.endswith(b"\r\n"):
                raise SmokeFailure("invalid bulk-string terminator")
            return header + payload
        if marker in (b"*", b"%", b"~", b"|", b">"):
            line = self.line()
            if line == b"?":
                result = bytearray(marker + b"?\r\n")
                while True:
                    peek = self.exact(1)
                    if peek == b".":
                        if self.line():
                            raise SmokeFailure("invalid streamed aggregate terminator")
                        result.extend(b".\r\n")
                        return bytes(result)
                    result.extend(self.frame(peek))
            count = int(line)
            result = bytearray(marker + line + b"\r\n")
            if count < 0:
                return bytes(result)
            child_count = count * (2 if marker in (b"%", b"|") else 1)
            for _ in range(child_count):
                result.extend(self.frame())
            return bytes(result)
        raise SmokeFailure(f"unsupported RESP response marker {marker!r}")


def command(*args: bytes) -> bytes:
    return b"*" + str(len(args)).encode() + b"\r\n" + b"".join(
        b"$" + str(len(arg)).encode() + b"\r\n" + arg + b"\r\n"
        for arg in args
    )


def server_args(binary: Path, tempdir: str) -> list[str]:
    return [
        str(binary), "--bind", "127.0.0.1", "--protected-mode", "yes",
        "--port", str(PORT), "--daemonize", "no", "--loglevel", "warning",
        "--requirepass", "resp-benchmark-pass",
        "--save", "", "--appendonly", "no", "--dir", tempdir,
    ]


def connect_ready(proc: subprocess.Popen[bytes]) -> socket.socket:
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise SmokeFailure(f"Redis exited during startup with {proc.returncode}")
        try:
            sock = socket.create_connection(("127.0.0.1", PORT), timeout=0.25)
            sock.settimeout(3)
            return sock
        except OSError:
            time.sleep(0.025)
    raise SmokeFailure(f"Redis did not listen on {PORT}")


def run_one(build: str, binary: Path, protocol: int, repetition: int,
            output_dir: Path) -> str:
    tag = f"{build}-resp{protocol}-run{repetition:02d}"
    log_path = output_dir / f"{tag}.log"
    transcript_path = output_dir / f"{tag}.json"
    transcript: list[dict[str, str]] = []
    with tempfile.TemporaryDirectory(prefix="redis-smoke-") as tempdir, log_path.open("wb") as log:
        proc = subprocess.Popen(
            server_args(binary, tempdir), stdout=log, stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        sock: socket.socket | None = None
        try:
            sock = connect_ready(proc)
            reader = RESPReader(sock)

            def exchange(args: tuple[bytes, ...], expected: bytes | None = None,
                         normalize: bool = False) -> bytes:
                request = command(*args)
                sock.sendall(request)
                response = reader.frame()
                if expected is not None and response != expected:
                    raise SmokeFailure(
                        f"{tag}: {args!r} returned {response!r}; expected {expected!r}"
                    )
                stored = b"<RESP3_HELLO_MAP>" if normalize else response
                transcript.append({"request_hex": request.hex(), "response_hex": stored.hex()})
                return response

            noauth = exchange((b"PING",))
            if not noauth.startswith(b"-NOAUTH "):
                raise SmokeFailure(f"{tag}: unauthenticated PING was not rejected: {noauth!r}")
            wrongpass = exchange((b"AUTH", b"default", b"incorrect"))
            if not wrongpass.startswith(b"-WRONGPASS "):
                raise SmokeFailure(f"{tag}: bad password was not rejected: {wrongpass!r}")
            exchange((b"AUTH", b"default", b"resp-benchmark-pass"), b"+OK\r\n")
            if protocol == 3:
                hello = exchange((b"HELLO", b"3"), normalize=True)
                if not hello.startswith(b"%") or b"proto" not in hello or b":3\r\n" not in hello:
                    raise SmokeFailure(f"{tag}: HELLO 3 did not return a RESP3 map: {hello!r}")
            exchange((b"PING",), b"+PONG\r\n")
            exchange((b"SET", b"bench:key", b"value"), b"+OK\r\n")
            exchange((b"GET", b"bench:key"), b"$5\r\nvalue\r\n")
            exchange((b"INCR", b"bench:counter"), b":1\r\n")
            exchange((b"HSET", b"bench:hash", b"field", b"value"), b":1\r\n")
            hgetall = exchange((b"HGETALL", b"bench:hash"))
            if protocol == 2 and hgetall != b"*2\r\n$5\r\nfield\r\n$5\r\nvalue\r\n":
                raise SmokeFailure(f"{tag}: unexpected RESP2 HGETALL: {hgetall!r}")
            if protocol == 3 and not hgetall.startswith(b"%1\r\n"):
                raise SmokeFailure(f"{tag}: expected RESP3 map from HGETALL: {hgetall!r}")

            exchange((b"MULTI",), b"+OK\r\n")
            exchange((b"SET", b"tx:key", b"value"), b"+QUEUED\r\n")
            exchange((b"INCR", b"tx:counter"), b"+QUEUED\r\n")
            exec_reply = exchange((b"EXEC",))
            if not exec_reply.startswith(b"*2\r\n"):
                raise SmokeFailure(f"{tag}: EXEC did not return its two transaction results: {exec_reply!r}")

            encoded = json.dumps(transcript, indent=2) + "\n"
            transcript_path.write_text(encoded, encoding="utf-8")
            return hashlib.sha256(encoded.encode()).hexdigest()
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
            if proc.returncode != 0:
                raise SmokeFailure(f"{tag}: Redis shutdown returned {proc.returncode}; see {log_path}")
            log_data = log_path.read_bytes()
            if b"AddressSanitizer:" in log_data or b"runtime error:" in log_data:
                raise SmokeFailure(f"{tag}: sanitizer report found; see {log_path}")


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: protocol_smoke.py OUTPUT_DIR", file=sys.stderr)
        return 2
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    builds = {
        "reference": Path(os.environ.get("REDIS_REFERENCE_BIN", "")),
        "afl": Path(os.environ.get("REDIS_AFL_BIN", "")),
    }
    for name, path in builds.items():
        if not path.is_file():
            raise SystemExit(f"{name} Redis server missing: {path}")
    if not 1 <= REPETITIONS <= 100:
        raise SystemExit("REDIS_SMOKE_REPETITIONS must be between 1 and 100")

    results: dict[str, dict[str, list[str]]] = {}
    for build, binary in builds.items():
        results[build] = {}
        for protocol in (2, 3):
            hashes = [
                run_one(build, binary, protocol, index + 1, out)
                for index in range(REPETITIONS)
            ]
            if len(set(hashes)) != 1:
                raise SmokeFailure(f"{build} RESP{protocol} transcripts varied: {hashes}")
            results[build][f"resp{protocol}"] = hashes

    for protocol in (2, 3):
        reference = results["reference"][f"resp{protocol}"][0]
        instrumented = results["afl"][f"resp{protocol}"][0]
        if reference != instrumented:
            raise SmokeFailure(
                f"RESP{protocol} reference/AFL transcript hash mismatch: "
                f"{reference} != {instrumented}"
            )

    summary = {
        "repetitions_per_build_and_protocol": REPETITIONS,
        "protocol_versions": {"resp2": "RESP2", "resp3": "RESP3"},
        "transcript_hashes": results,
        "transcripts_and_logs": str(out),
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: RESP2/RESP3 PING, SET, GET, INCR, HSET, HGETALL; {REPETITIONS} fresh servers per build/protocol.")
    print(f"Reference and ASan transcript hashes match; evidence={out}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, EOFError, TimeoutError, ValueError, SmokeFailure) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
