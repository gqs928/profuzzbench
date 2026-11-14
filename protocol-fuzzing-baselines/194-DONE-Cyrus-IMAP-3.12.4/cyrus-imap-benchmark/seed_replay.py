#!/usr/bin/env python3
"""Replay every IMAP seed command-by-command and save response evidence."""

from __future__ import annotations

import base64
import json
import os
import re
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path


CRLF = b"\r\n"
PORT = int(os.environ.get("IMAP_PORT", "1143"))
LITERAL_AT_END = re.compile(rb"\{([0-9]+)(\+)?\}$")


def response_state(line: bytes) -> tuple[int, str]:
    line = line.lstrip(b" \t")
    if not line:
        return 0, "empty"
    if line.startswith(b"+"):
        return 20, "+ continuation"
    if line.startswith(b"*"):
        atoms = line[1:].strip().split()
        if not atoms:
            return 30, "* <empty>"
        if atoms[0].upper() in (b"OK", b"NO", b"BAD", b"BYE"):
            status = atoms[0].upper()
            return {b"OK": 1, b"NO": 2, b"BAD": 3, b"BYE": 4}[status], f"* {status.decode()}"
        if atoms[0][:1].isdigit() and len(atoms) > 1:
            atom = atoms[1]
        else:
            atom = atoms[0]
        return _atom_state(atom), f"* {atom.decode('ascii', 'replace').upper()}"
    atoms = line.split()
    if len(atoms) < 2:
        return 30, "tagged <missing-status>"
    status = atoms[1].upper()
    if status in (b"OK", b"NO", b"BAD", b"BYE"):
        return {b"OK": 10, b"NO": 11, b"BAD": 12, b"BYE": 13}[status], f"tagged {status.decode()}"
    return _atom_state(status), f"tagged {status.decode('ascii', 'replace').upper()}"


def _atom_state(atom: bytes) -> int:
    value = 2166136261
    for byte in atom.upper():
        value = ((value ^ byte) * 16777619) & 0xFFFFFFFF
    return 100 + value % 60000


def response_states(data: bytes) -> list[dict[str, object]]:
    """Classify response lines while skipping opaque IMAP literal payloads."""
    states: list[dict[str, object]] = []
    pos = 0
    while pos < len(data):
        end = data.find(CRLF, pos)
        if end < 0:
            break
        line = data[pos:end]
        state, label = response_state(line)
        states.append({"id": state, "label": label})
        marker = LITERAL_AT_END.search(line)
        pos = end + 2
        if marker:
            length = int(marker.group(1))
            if pos + length > len(data):
                break
            pos += length
    return states


def request_frame(data: bytes, start: int) -> tuple[bytes, bytes, bool]:
    """Return (frame, first-line, complete); honor one trailing IMAP literal."""
    line_end = data.find(CRLF, start)
    if line_end < 0:
        return data[start:], data[start:], False
    line = data[start:line_end]
    header_end = line_end + 2
    literal = LITERAL_AT_END.search(line)
    if not literal:
        return data[start:header_end], line, True
    payload_end = header_end + int(literal.group(1))
    if payload_end > len(data):
        return data[start:], line, False
    command_end = data.find(CRLF, payload_end)
    if command_end < 0:
        return data[start:], line, False
    return data[start:command_end + 2], line, True


class Connection:
    def __init__(self, sock: socket.socket):
        self.sock = sock
        self.pending = bytearray()

    def read_greeting(self, timeout: float = 5.0) -> bytes:
        self.sock.settimeout(timeout)
        while CRLF not in self.pending:
            chunk = self.sock.recv(65536)
            if not chunk:
                raise ConnectionError("server closed before greeting")
            self.pending.extend(chunk)
        end = self.pending.index(CRLF) + 2
        result = bytes(self.pending[:end])
        del self.pending[:end]
        return result

    def read_reply(self, tag: bytes, continuation: bool = False,
                   timeout: float = 4.0) -> bytes:
        self.sock.settimeout(timeout)
        pattern = re.compile(rb"(?:^|\r\n)" + re.escape(tag) + rb" [^\r\n]*\r\n")
        while True:
            current = bytes(self.pending)
            if continuation:
                first_end = current.find(CRLF)
                if first_end >= 0 and current[:1] == b"+":
                    result = current[:first_end + 2]
                    del self.pending[:first_end + 2]
                    return result
            match = pattern.search(current)
            if match:
                result = current[:match.end()]
                del self.pending[:match.end()]
                return result
            chunk = self.sock.recv(65536)
            if not chunk:
                raise ConnectionError(f"server closed before tagged response {tag!r}")
            self.pending.extend(chunk)


def start_server(prefix: Path, log_path: Path) -> tuple[subprocess.Popen[bytes], Connection]:
    subprocess.run(["/workspace/reset-state.sh"], check=True)
    env = os.environ.copy()
    env["CYRUS_PREFIX"] = str(prefix)
    env["PATH"] = f"{prefix}/bin:{prefix}/sbin:{prefix}/libexec:{env.get('PATH', '')}"
    env["LD_LIBRARY_PATH"] = f"{prefix}/lib:{env.get('LD_LIBRARY_PATH', '')}"
    with log_path.open("wb") as log:
        proc = subprocess.Popen(
            ["/workspace/start-server.sh"], stdout=log,
            stderr=subprocess.STDOUT, env=env, start_new_session=True,
        )
    deadline = time.monotonic() + 12
    last_error = ""
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(f"server exited during startup ({proc.returncode}); {log_path}")
        try:
            sock = socket.create_connection(("127.0.0.1", PORT), timeout=0.3)
            conn = Connection(sock)
            conn.greeting = conn.read_greeting()
            return proc, conn
        except (OSError, TimeoutError, ConnectionError) as exc:
            last_error = str(exc)
            time.sleep(0.05)
    raise RuntimeError(f"server did not start on {PORT}: {last_error}; {log_path}")


def stop_server(proc: subprocess.Popen[bytes]) -> int:
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
    return proc.returncode or 0


def replay_seed(path: Path, prefix: Path, output_dir: Path, round_no: int) -> dict[str, object]:
    proc, conn = start_server(prefix, output_dir / f"round-{round_no:02d}-{path.name}.server.log")
    transcript: list[bytes] = [conn.greeting]
    steps: list[dict[str, object]] = []
    data = path.read_bytes()
    offset = 0
    try:
        while offset < len(data):
            frame, first_line, complete = request_frame(data, offset)
            if not frame:
                break
            parts = first_line.split(None, 1)
            tag = parts[0] if parts else b"?"
            literal = LITERAL_AT_END.search(first_line)
            step: dict[str, object] = {
                "tag": tag.decode("ascii", "replace"),
                "command": first_line.decode("utf-8", "replace"),
                "request_base64": base64.b64encode(frame).decode("ascii"),
                "complete_request": complete,
                "responses_base64": [],
            }
            responses: list[bytes] = []
            try:
                if literal and not literal.group(2):
                    header_length = len(first_line) + 2
                    conn.sock.sendall(frame[:header_length])
                    prompt = conn.read_reply(tag, continuation=True, timeout=2.0)
                    responses.append(prompt)
                    if prompt.startswith(b"+"):
                        conn.sock.sendall(frame[header_length:])
                        responses.append(conn.read_reply(tag, timeout=4.0))
                    else:
                        step["sync_literal_rejected"] = True
                else:
                    conn.sock.sendall(frame)
                    if complete:
                        responses.append(conn.read_reply(tag, timeout=4.0))
                    else:
                        conn.sock.settimeout(0.35)
                        try:
                            responses.append(conn.sock.recv(65536))
                        except socket.timeout:
                            step["partial_input_no_response"] = True
                step["status"] = "complete" if complete else "truncated_input"
            except (OSError, TimeoutError, ConnectionError) as exc:
                step["status"] = "connection_error"
                step["error"] = str(exc)
            step["responses_base64"] = [base64.b64encode(item).decode("ascii") for item in responses]
            step["response_states"] = [state for response in responses for state in response_states(response)]
            transcript.extend(responses)
            steps.append(step)
            offset += len(frame)
            if (not complete or step.get("status") == "connection_error" or
                    step.get("sync_literal_rejected")):
                break
        return {
            "round": round_no,
            "seed": path.name,
            "input_bytes": len(data),
            "greeting_base64": base64.b64encode(conn.greeting).decode("ascii"),
            "steps": steps,
            "response_states": [state for response in transcript for state in response_states(response)],
            "server_log": f"round-{round_no:02d}-{path.name}.server.log",
        }
    finally:
        conn.sock.close()
        stop_server(proc)


def main() -> int:
    if len(sys.argv) != 5:
        print("usage: seed_replay.py SEEDS_DIR OUTPUT_DIR PREFIX REPETITIONS", file=sys.stderr)
        return 2
    seeds_dir, output_dir, prefix = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    repetitions = int(sys.argv[4])
    if repetitions < 2:
        raise ValueError("at least two repetitions are required for a repeatability check")
    if not seeds_dir.is_dir() or not (prefix / "libexec" / "master").exists():
        raise RuntimeError("seed directory or selected Cyrus build is missing")
    output_dir.mkdir(parents=True, exist_ok=True)
    seeds = sorted(item for item in seeds_dir.iterdir() if item.is_file())
    if not seeds:
        raise RuntimeError(f"no seed files in {seeds_dir}")

    results: list[dict[str, object]] = []
    for round_no in range(1, repetitions + 1):
        for seed in seeds:
            results.append(replay_seed(seed, prefix, output_dir, round_no))

    signatures: dict[str, list[list[int]]] = {}
    label_map: dict[str, set[str]] = {}
    for item in results:
        ids = [int(state["id"]) for state in item["response_states"]]
        signatures.setdefault(str(item["seed"]), []).append(ids)
        for state in item["response_states"]:
            label_map.setdefault(str(state["id"]), set()).add(str(state["label"]))
    label_map.setdefault("0", set()).add("initial response-state sentinel")
    stable = {seed: len({tuple(seq) for seq in sequences}) == 1 for seed, sequences in signatures.items()}
    report = {
        "protocol": "IMAP4rev1",
        "server_build": str(prefix),
        "repetitions": repetitions,
        "seed_count": len(seeds),
        "session_count": len(results),
        "all_normalized_state_sequences_stable": all(stable.values()),
        "stable_seed_count": sum(stable.values()),
        "state_signatures": signatures,
        "state_labels": {key: sorted(value) for key, value in sorted(label_map.items(), key=lambda pair: int(pair[0]))},
        "sessions": results,
    }
    (output_dir / "seed-replay.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if not report["all_normalized_state_sequences_stable"]:
        print("WARNING: one or more normalized response-state sequences varied", file=sys.stderr)
    print(f"Replayed {len(seeds)} seeds for {repetitions} clean rounds; stable={report['stable_seed_count']}/{len(seeds)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
