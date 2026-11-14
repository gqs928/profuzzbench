#!/usr/bin/env python3
"""Exercise a basic IRC session against the clean and instrumented builds."""
from pathlib import Path
import hashlib
import json
import os
import re
import socket
import subprocess
import sys
import time

WORKDIR = Path("/home/ubuntu/experiments")
PORT = 6667


class IRCConnection:
    def __init__(self, sock: socket.socket):
        self.sock = sock
        self.pending = bytearray()
        self.transcript = bytearray()

    def until(self, marker: bytes, timeout: float = 8.0) -> bytes:
        deadline = time.monotonic() + timeout
        while marker not in self.pending:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise RuntimeError(f"timeout waiting for {marker!r}: {bytes(self.pending)!r}")
            self.sock.settimeout(remaining)
            try:
                block = self.sock.recv(65536)
            except socket.timeout as exc:
                raise RuntimeError(f"timeout waiting for {marker!r}") from exc
            if not block:
                raise RuntimeError(f"server closed before {marker!r}: {bytes(self.pending)!r}")
            self.pending.extend(block)
        end = self.pending.index(marker) + len(marker)
        data = bytes(self.pending[:end])
        del self.pending[:end]
        self.transcript.extend(data)
        return data

    def send(self, command: str) -> None:
        self.sock.sendall(command.encode("ascii") + b"\r\n")


def exercise(kind: str, out_dir: Path) -> dict:
    target_dir = WORKDIR / f"inspircd-{kind}"
    target = target_dir / "run" / "bin" / "inspircd"
    config = target_dir / "run" / "conf" / "inspircd.conf"
    log_path = out_dir / f"{kind}.server.log"
    transcript_path = out_dir / f"{kind}.transcript.bin"
    log = log_path.open("wb")
    proc = subprocess.Popen(
        [str(target), "-F", "-L", "-P", "-c", str(config)],
        cwd=target_dir,
        stdout=log,
        stderr=subprocess.STDOUT,
        env={**os.environ, "ASAN_OPTIONS": "abort_on_error=1:symbolize=0:detect_leaks=0"},
    )
    conn = None
    try:
        deadline = time.monotonic() + 10
        while True:
            if proc.poll() is not None:
                raise RuntimeError(f"{kind} server exited {proc.returncode}; see {log_path}")
            try:
                probe = socket.create_connection(("127.0.0.1", PORT), timeout=0.2)
                probe.close()
                break
            except OSError:
                if time.monotonic() >= deadline:
                    raise RuntimeError(f"{kind} server did not listen on {PORT}; see {log_path}")
                time.sleep(0.05)

        conn = IRCConnection(socket.create_connection(("127.0.0.1", PORT), timeout=3))
        conn.send("NICK fuzzuser")
        conn.send("USER fuzzuser 0 * :Benchmark User")
        conn.until(b" 001 ")
        conn.send("PING :smoke-token")
        conn.until(b" PONG ")
        conn.send("VERSION")
        conn.until(b" 351 ")
        conn.send("JOIN #bench")
        conn.until(b" 366 ")
        conn.send("TOPIC #bench :reproducible topic")
        conn.until(b" TOPIC #bench :reproducible topic")
        conn.send("NAMES #bench")
        conn.until(b" 366 ")
        conn.send("PART #bench :finished")
        conn.until(b" PART #bench")
        conn.send("QUIT :done")

        transcript = bytes(conn.transcript)
        transcript_path.write_bytes(transcript)
        numeric_codes = [int(code) for code in re.findall(rb" (?P<code>[0-9]{3}) ", transcript)]
        required = [b" PONG ", b" 351 ", b" TOPIC #bench", b" PART #bench"]
        missing = [marker.decode("ascii") for marker in required if marker not in transcript]
        # IRC serializers may encode the final channel argument as either
        # "JOIN #bench" or "JOIN :#bench". Check the command/argument, not
        # one particular valid wire spelling.
        join_seen = any(
            re.search(rb"(?:^|[ ])JOIN[ \t]+:?#bench(?:[ \t]|$)", line)
            for line in transcript.splitlines()
        )
        if not join_seen:
            missing.append("JOIN #bench")
        if missing or 1 not in numeric_codes or 351 not in numeric_codes or 353 not in numeric_codes or 366 not in numeric_codes:
            raise RuntimeError(f"{kind} protocol assertions failed; missing={missing}, numeric={numeric_codes}")
        return {
            "build": kind,
            "numeric_codes": numeric_codes,
            "response_sha256": hashlib.sha256(transcript).hexdigest(),
            "transcript": str(transcript_path),
        }
    finally:
        if conn is not None:
            conn.sock.close()
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)
        log.close()
        if kind == "afl":
            server_log = log_path.read_bytes()
            if b"ERROR: AddressSanitizer" in server_log or b"runtime error:" in server_log:
                raise RuntimeError(
                    f"{kind} server reported a sanitizer error, including during shutdown; "
                    f"see {log_path}"
                )


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: protocol_smoke.py OUTPUT_DIR", file=sys.stderr)
        return 2
    out_dir = Path(sys.argv[1])
    out_dir.mkdir(parents=True, exist_ok=True)
    reference = exercise("reference", out_dir)
    instrumented = exercise("afl", out_dir)
    if reference["numeric_codes"] != instrumented["numeric_codes"]:
        raise SystemExit(
            "FAIL: reference and instrumented protocol numeric-state sequences differ: "
            f"{reference['numeric_codes']} != {instrumented['numeric_codes']}"
        )
    report = {"reference": reference, "instrumented": instrumented}
    (out_dir / "summary.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("PASS: normal IRC registration, PING/PONG, VERSION, JOIN/NAMES, TOPIC and PART.")
    print(f"reference_version-response_sha256={reference['response_sha256']}")
    print(f"instrumented_response_sha256={instrumented['response_sha256']}")
    print(f"numeric_codes={reference['numeric_codes']}")
    print(f"transcripts={out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
