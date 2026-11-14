#!/usr/bin/env python3
"""Add the loopback TLS listener required by UnrealIRCd's config validator."""
from pathlib import Path
import re
import sys


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: make_tls_config.py INPUT_CONF OUTPUT_CONF", file=sys.stderr)
        return 2
    source, destination = map(Path, sys.argv[1:])
    text = source.read_text(encoding="utf-8")
    listener = re.compile(
        r"listen\s*\{\s*ip 127\.0\.0\.1;\s*port 6667;\s*\}", re.MULTILINE)
    replacement = (
        "listen {\n\tip 127.0.0.1;\n\tport 6667;\n}\n\n"
        "listen {\n\tip 127.0.0.1;\n\tport 6697;\n\toptions { tls; }\n}"
    )
    text, count = listener.subn(replacement, text, count=1)
    if count != 1 or len(re.findall(r"(?m)^\s*port 6697;", text)) != 1:
        raise SystemExit("could not add the single loopback TLS listener")
    set_block = re.compile(r"(?m)^set \{\n\tconnthrottle \{")
    text, count = set_block.subn(
        'set {\n\ttls {\n\t\tcertificate "tls/server.cert.pem";\n'
        '\t\tkey "tls/server.key.pem";\n\t}\n\tconnthrottle {',
        text,
        count=1,
    )
    if count != 1:
        raise SystemExit("could not set the self-signed loopback TLS certificate paths")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
