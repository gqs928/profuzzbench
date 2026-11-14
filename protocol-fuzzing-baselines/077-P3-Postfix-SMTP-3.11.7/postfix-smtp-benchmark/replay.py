#!/usr/bin/env python3
"""Replay AFLNet queue entries as bounded SMTP command/response sequences."""

import argparse
import json
import re
import socket
import subprocess
from pathlib import Path


SMTP_CODE = re.compile(rb"^(\d{3})([- ])")
LENGTH_PREFIXED_DIRS = {"replayable-queue", "replayable-new-ipsm-paths"}


def split_smtp_requests(data):
    """Split SMTP commands while preserving an entire DATA transaction."""
    requests = []
    position = 0
    while position < len(data):
        line_end = data.find(b"\r\n", position)
        if line_end < 0:
            requests.append((data[position:], False))
            break
        command_end = line_end + 2
        command = data[position:line_end]
        is_data = command[:4].upper() == b"DATA" and (
            len(command) == 4 or command[4:5] in (b" ", b"\t")
        )
        request_end = command_end
        if is_data:
            scan = command_end
            terminator_end = None
            while scan < len(data):
                if data.startswith(b".\r\n", scan) and (
                    scan == command_end or data[scan - 2:scan] == b"\r\n"
                ):
                    terminator_end = scan + 3
                    break
                next_end = data.find(b"\r\n", scan)
                if next_end < 0:
                    break
                scan = next_end + 2
            request_end = terminator_end if terminator_end is not None else len(data)
        requests.append((data[position:request_end], is_data))
        position = request_end
    return requests


def decode_aflnet_length_prefixed(data):
    """Decode AFLNet -E replay files (u32 little-endian length + request)."""
    position = 0
    requests = []
    while position < len(data):
        if position + 4 > len(data):
            return None
        size = int.from_bytes(data[position : position + 4], "little")
        position += 4
        if size > len(data) - position:
            return None
        requests.append(data[position : position + size])
        position += size
    return requests if requests else None


def is_data_command(request):
    line = request.split(b"\r\n", 1)[0]
    return line[:4].upper() == b"DATA" and (
        len(line) == 4 or line[4:5] in (b" ", b"\t")
    )


def read_smtp_reply(sock, byte_limit=65536):
    """Read one complete SMTP reply, including any 3-digit hyphen lines."""
    reply = bytearray()
    expected_code = None
    while len(reply) < byte_limit:
        line = bytearray()
        while len(reply) + len(line) < byte_limit and not line.endswith(b"\n"):
            chunk = sock.recv(1)
            if not chunk:
                return bytes(reply + line)
            line.extend(chunk)
        if not line:
            break
        reply.extend(line)
        match = SMTP_CODE.match(line)
        if not match or match.group(2) != b"-":
            break
        expected_code = match.group(1)
    return bytes(reply)


def reply_code(reply):
    match = SMTP_CODE.match(reply.splitlines()[0]) if reply else None
    return match.group(1).decode("ascii") if match else None


def find_queue(root):
    files = []
    root = Path(root)
    for name in ("queue", "replayable-queue", "replayable-new-ipsm-paths"):
        for queue in sorted(root.rglob(name)):
            files.extend(path for path in queue.iterdir() if path.is_file() and not path.name.startswith("."))
    return sorted(set(files))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--aflnet-output", required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=2525)
    parser.add_argument("--timeout", type=float, default=1.0)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    paths = find_queue(args.aflnet_output)
    totals = {
        "queue_files": len(paths),
        "connected": 0,
        "smtp_greeting_220": 0,
        "requests_sent": 0,
        "data_transactions": 0,
        "data_354_replies": 0,
        "received_reply_bytes": 0,
        "reply_timeouts": 0,
        "connection_errors": 0,
        "target_master_alive": None,
    }
    cases = []
    for path in paths:
        item = {
            "file": str(path.relative_to(args.aflnet_output)),
            "bytes": path.stat().st_size,
            "requests": [],
        }
        try:
            with socket.create_connection((args.host, args.port), timeout=args.timeout) as sock:
                sock.settimeout(args.timeout)
                greeting = read_smtp_reply(sock)
                item["greeting"] = greeting.decode("ascii", "replace")[:512].rstrip()
                totals["connected"] += 1
                totals["received_reply_bytes"] += len(greeting)
                if reply_code(greeting) == "220":
                    totals["smtp_greeting_220"] += 1
                contents = path.read_bytes()
                if path.parent.name in LENGTH_PREFIXED_DIRS:
                    decoded = decode_aflnet_length_prefixed(contents)
                    if decoded is None:
                        raise ValueError("invalid AFLNet -E length-prefixed replay file")
                    item["input_format"] = "aflnet-u32le-length-prefixed-requests"
                    requests = [(request, is_data_command(request)) for request in decoded]
                else:
                    item["input_format"] = "raw-smtp-byte-stream"
                    requests = split_smtp_requests(contents)
                for request, is_data in requests:
                    if not request:
                        continue
                    entry = {"bytes": len(request), "data_transaction": is_data}
                    totals["requests_sent"] += 1
                    if is_data:
                        totals["data_transactions"] += 1
                        command_end = request.find(b"\r\n") + 2
                        command = request[:command_end]
                        body = request[command_end:]
                        sock.sendall(command)
                        try:
                            replies = [read_smtp_reply(sock)]
                        except socket.timeout:
                            replies = [b""]
                        if reply_code(replies[0]) == "354":
                            totals["data_354_replies"] += 1
                            if body:
                                sock.sendall(body)
                                try:
                                    replies.append(read_smtp_reply(sock))
                                except socket.timeout:
                                    replies.append(b"")
                                    totals["reply_timeouts"] += 1
                    else:
                        sock.sendall(request)
                        try:
                            replies = [read_smtp_reply(sock)]
                        except socket.timeout:
                            replies = [b""]
                    if not replies[0]:
                        totals["reply_timeouts"] += 1
                        entry["classification"] = "no reply before bounded timeout/close"
                    else:
                        codes = [reply_code(replies[0])]
                        codes.extend(reply_code(reply) for reply in replies[1:])
                        entry["reply_codes"] = codes
                        entry["reply_sample"] = b"".join(replies)[:512].decode("ascii", "replace")
                        entry["classification"] = "SMTP reply observed"
                        totals["received_reply_bytes"] += sum(map(len, replies))
                        if codes[-1] == "221":
                            item["requests"].append(entry)
                            break
                    item["requests"].append(entry)
        except (OSError, RuntimeError, ValueError) as error:
            item["error"] = str(error)
            item["classification"] = "connection/replay error"
            totals["connection_errors"] += 1
        cases.append(item)

    check = subprocess.run(
        ["/usr/sbin/postfix", "status"],
        env={"MAIL_CONFIG": "/etc/postfix"},
        capture_output=True,
        text=True,
    )
    totals["master_test_exit_code"] = check.returncode
    totals["target_master_alive"] = check.returncode == 0
    failures = []
    if totals["connected"] != totals["queue_files"]:
        failures.append("not every queue item connected to the SMTP listener")
    if totals["smtp_greeting_220"] != totals["queue_files"]:
        failures.append("not every queue item received an SMTP 220 greeting")
    if totals["reply_timeouts"]:
        failures.append("one or more SMTP replies timed out")
    if totals["connection_errors"]:
        failures.append("one or more queue items failed to replay")
    if not totals["target_master_alive"]:
        failures.append("Postfix master did not remain healthy after queue replay")
    result = {
        "implementation": "Postfix 3.11.7",
        "scope": "AFLNet SMTP command sequences; SMTP DATA plus message body and terminator are one replay request",
        "timeout_seconds": args.timeout,
        "acceptance": {"pass": not failures, "failures": failures},
        "totals": totals,
        "cases": cases,
    }
    Path(args.output).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
