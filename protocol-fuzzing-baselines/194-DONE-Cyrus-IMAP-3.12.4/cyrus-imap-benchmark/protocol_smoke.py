#!/usr/bin/env python3
"""Check repeated IMAP authentication, mailbox and literal command sessions."""

from __future__ import annotations

import base64
import json
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path


PORT = int(os.environ.get("IMAP_PORT", "1143"))
PASSWORD = b"resp-benchmark-pass"
MESSAGE = (
    b"From: bench@example.invalid\r\n"
    b"To: fuzzuser@localhost\r\n"
    b"Subject: IMAP benchmark seed\r\n\r\n"
    b"A small fixed message body.\r\n"
)


class IMAPConnection:
    def __init__(self, sock: socket.socket):
        self.sock = sock
        self.sock.settimeout(4)
        self.pending = bytearray()

    def _read_line(self) -> bytes:
        deadline = time.monotonic() + 4
        while True:
            split = self.pending.find(b"\r\n")
            if split >= 0:
                line = bytes(self.pending[: split + 2])
                del self.pending[: split + 2]
                return line
            if time.monotonic() >= deadline:
                raise TimeoutError("timed out waiting for IMAP response line")
            chunk = self.sock.recv(65536)
            if not chunk:
                raise ConnectionError("IMAP server closed the session")
            self.pending.extend(chunk)

    def greeting(self) -> bytes:
        return self._read_line()

    def send_tagged(self, tag: str, command: str) -> bytes:
        self.sock.sendall(f"{tag} {command}\r\n".encode("ascii"))
        try:
            return self.read_tagged(tag)
        except TimeoutError as exc:
            raise TimeoutError(f"waiting for {tag} {command}: {exc}") from exc

    def read_continuation(self, tag: str) -> bytes:
        response = bytearray()
        tagged = tag.encode("ascii") + b" "
        while True:
            line = self._read_line()
            response.extend(line)
            if line.startswith(b"+") or line.startswith(tagged):
                return bytes(response)

    def read_tagged(self, tag: str) -> bytes:
        response = bytearray()
        prefix = tag.encode("ascii") + b" "
        while True:
            line = self._read_line()
            response.extend(line)
            if line.startswith(prefix):
                return bytes(response)


def start_server(prefix: Path, log_path: Path) -> tuple[subprocess.Popen[bytes], IMAPConnection]:
    subprocess.run(["/workspace/reset-state.sh"], check=True)
    env = os.environ.copy()
    env["CYRUS_PREFIX"] = str(prefix)
    with log_path.open("wb") as log:
        proc = subprocess.Popen(
            ["/workspace/start-server.sh"], stdout=log, stderr=subprocess.STDOUT,
            env=env, start_new_session=True,
        )
    deadline = time.monotonic() + 12
    last_error = ""
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(f"master exited during startup ({proc.returncode}); log={log_path}")
        try:
            sock = socket.create_connection(("127.0.0.1", PORT), timeout=0.3)
            conn = IMAPConnection(sock)
            greeting = conn.greeting()
            if b"* OK" not in greeting.upper() and b"* PREAUTH" not in greeting.upper():
                raise RuntimeError(f"unexpected server greeting: {greeting!r}")
            conn.initial_greeting = greeting
            return proc, conn
        except (OSError, TimeoutError, ConnectionError) as exc:
            last_error = str(exc)
            time.sleep(0.05)
    raise RuntimeError(f"server did not listen on {PORT}: {last_error}; log={log_path}")


def stop_server(proc: subprocess.Popen[bytes]) -> None:
    if proc.poll() is None:
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait(timeout=5)
    subprocess.run(["/workspace/reset-state.sh"], check=True)


def status_ok(tag: str, response: bytes) -> bool:
    return any(line.startswith(tag.encode("ascii") + b" OK") for line in response.split(b"\r\n"))


def exercise(prefix: Path, index: int, log_dir: Path) -> dict[str, object]:
    proc, conn = start_server(prefix, log_dir / f"{prefix.name}-{index:02d}.server.log")
    transcript: list[bytes] = [conn.initial_greeting]
    try:
        responses = [
            conn.send_tagged("A01", "CAPABILITY"),
            conn.send_tagged("A02", "NOOP"),
            conn.send_tagged("A03", "LOGIN fuzzuser wrong-password"),
            conn.send_tagged("A04", "LOGIN fuzzuser resp-benchmark-pass"),
            conn.send_tagged("A05", "CAPABILITY"),
            conn.send_tagged("A06", "CREATE INBOX"),
        ]
        transcript.extend(responses)
        checks = {
            "capability_prelogin": b"CAPABILITY" in responses[0].upper(),
            "noop": status_ok("A02", responses[1]),
            "wrong_password_rejected": any(
                line.startswith(b"A03 NO") for line in responses[2].split(b"\r\n")
            ),
            "login": status_ok("A04", responses[3]),
            "capability_postlogin": b"CAPABILITY" in responses[4].upper(),
            "create_inbox": status_ok("A06", responses[5]),
        }
        if not checks["login"]:
            raise RuntimeError(f"SASL LOGIN failed: {responses[3]!r}")
        if not checks["create_inbox"]:
            raise RuntimeError(f"CREATE INBOX failed: {responses[5]!r}")

        conn.sock.sendall(f"A07 APPEND INBOX {{{len(MESSAGE)}}}\r\n".encode("ascii"))
        continuation = conn.read_continuation("A07")
        transcript.append(continuation)
        if not continuation.startswith(b"+"):
            raise RuntimeError(f"APPEND did not issue continuation: {continuation!r}")
        conn.sock.sendall(MESSAGE + b"\r\n")
        append_result = conn.read_tagged("A07")
        transcript.append(append_result)
        checks["append_literal"] = status_ok("A07", append_result)
        if not checks["append_literal"]:
            raise RuntimeError(f"APPEND literal failed: {append_result!r}")

        rest = [
            conn.send_tagged("A08", "SELECT INBOX"),
            conn.send_tagged("A09", "FETCH 1 (UID FLAGS BODY.PEEK[HEADER])"),
            conn.send_tagged("A10", "UID SEARCH ALL"),
            conn.send_tagged("A11", "LOGOUT"),
        ]
        transcript.extend(rest)
        checks.update({
            "select": status_ok("A08", rest[0]),
            "fetch": status_ok("A09", rest[1]) and b"FETCH" in rest[1].upper(),
            "uid_search": status_ok("A10", rest[2]),
            "logout": status_ok("A11", rest[3]),
        })
        failures = [key for key, value in checks.items() if not value]
        if failures:
            raise RuntimeError(f"IMAP smoke checks failed: {failures}")
        return {
            "variant": prefix.name,
            "session": index,
            "checks": checks,
            "transcript_base64": [base64.b64encode(item).decode("ascii") for item in transcript],
        }
    finally:
        conn.sock.close()
        stop_server(proc)


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: protocol_smoke.py OUTPUT_DIR REPETITIONS", file=sys.stderr)
        return 2
    output = Path(sys.argv[1])
    repetitions = int(sys.argv[2])
    if repetitions < 1:
        raise ValueError("REPETITIONS must be positive")
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise RuntimeError(f"output directory is not empty: {output}")

    variants = [
        Path(os.environ.get("CYRUS_REFERENCE_PREFIX", "/home/ubuntu/experiments/cyrus-reference")),
        Path(os.environ.get("CYRUS_AFL_PREFIX", "/home/ubuntu/experiments/cyrus-afl")),
    ]
    results: list[dict[str, object]] = []
    for prefix in variants:
        if not (prefix / "libexec" / "master").exists():
            raise RuntimeError(f"Cyrus master binary missing: {prefix}/libexec/master")
        for index in range(1, repetitions + 1):
            results.append(exercise(prefix, index, output))

    report = {
        "protocol": "IMAP4rev1",
        "port": PORT,
        "repetitions_per_build": repetitions,
        "sessions": len(results),
        "all_checks_passed": all(
            all(result["checks"].values()) for result in results
        ),
        "results": results,
    }
    (output / "protocol-smoke.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"PASS: IMAP LOGIN, literal APPEND, SELECT/FETCH/SEARCH and LOGOUT; "
        f"{len(results)} clean server sessions; evidence={output}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, TimeoutError, ConnectionError, ValueError, RuntimeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
