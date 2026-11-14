#!/usr/bin/env python3
"""Replay AFLNet's raw NETCONF request queue through the local SSH proxy."""
import json
import os
import pathlib
import socket
import sys
import time

ROOT = pathlib.Path(sys.argv[1])
HOST = os.environ.get("NETCONF_HOST", "127.0.0.1")
PORT = int(os.environ.get("NETCONF_PORT", "1830"))
END = b"]]>]]>"
files = sorted(p for p in ROOT.glob("**/queue/id:*") if p.is_file())
result = {"queue_files": len(files), "connected": 0, "response_bytes": 0,
          "response_frames": 0, "server_hellos": 0, "rpc_replies": 0,
          "rpc_errors": 0, "no_rpc_reply": 0, "no_response": 0, "timeouts": 0,
          "resets": 0, "errors": 0}

for path in files:
    received = bytearray()
    try:
        with socket.create_connection((HOST, PORT), timeout=5) as sock:
            result["connected"] += 1
            sock.settimeout(0.5)
            sock.sendall(path.read_bytes())
            deadline = time.monotonic() + 2.0
            while time.monotonic() < deadline:
                sock.settimeout(max(0.02, deadline - time.monotonic()))
                try:
                    part = sock.recv(65536)
                    if not part:
                        break
                    received.extend(part)
                except socket.timeout:
                    result["timeouts"] += 1
                    break
    except ConnectionResetError:
        result["resets"] += 1
    except (OSError, TimeoutError):
        result["errors"] += 1
    result["response_bytes"] += len(received)
    result["response_frames"] += received.count(END)
    result["server_hellos"] += received.count(b"<hello")
    replies = received.count(b"<rpc-reply")
    result["rpc_replies"] += replies
    result["rpc_errors"] += received.count(b"<rpc-error")
    if not replies:
        result["no_rpc_reply"] += 1
    if not received:
        result["no_response"] += 1

print(json.dumps(result, indent=2, sort_keys=True))
