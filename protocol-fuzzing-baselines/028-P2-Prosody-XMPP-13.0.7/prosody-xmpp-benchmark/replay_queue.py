#!/usr/bin/env python3
import json, pathlib, socket, sys, time
root = pathlib.Path(sys.argv[1])
files = sorted(p for p in root.glob("**/queue/id:*") if p.is_file())
result = {"queue_files": len(files), "connected": 0, "responses": 0, "timeouts": 0, "resets": 0, "errors": 0}
for path in files:
    try:
        with socket.create_connection(("127.0.0.1", 5222), timeout=3) as sock:
            result["connected"] += 1
            sock.settimeout(0.7)
            sock.sendall(path.read_bytes())
            deadline = time.monotonic() + 1.5
            received = b""
            while time.monotonic() < deadline:
                try:
                    part = sock.recv(8192)
                    if not part: break
                    received += part
                except socket.timeout:
                    result["timeouts"] += 1
                    break
            if received: result["responses"] += 1
    except ConnectionResetError:
        result["resets"] += 1
    except (OSError, TimeoutError):
        result["errors"] += 1
print(json.dumps(result, indent=2, sort_keys=True))
