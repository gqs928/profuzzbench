#!/usr/bin/env python3
import sys
from pathlib import Path

path = Path(sys.argv[1])
section = ""
ports = {
    "http": {"port": "0", "sslport": "0"},
    "rtmp": {"port": "0", "sslport": "0"},
    "rtp_proxy": {"port": "0"},
    "rtsp": {"port": "8554", "sslport": "0"},
    "srt": {"port": "0"},
    "onvif": {"port": "0"},
    "shell": {"port": "0"},
}
lines = []
for line in path.read_text(encoding="utf-8-sig").splitlines(keepends=True):
    stripped = line.strip()
    if stripped.startswith("[") and stripped.endswith("]"):
        section = stripped[1:-1].lower()
    elif stripped and not stripped.startswith(("#", ";")) and "=" in stripped:
        key = stripped.split("=", 1)[0].strip()
        if key in ports.get(section, {}):
            line = f"{key}={ports[section][key]}\n"
    lines.append(line)
path.write_text("".join(lines))
