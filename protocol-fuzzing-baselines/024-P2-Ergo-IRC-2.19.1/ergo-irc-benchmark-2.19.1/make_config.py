#!/usr/bin/env python3
"""Generate a loopback-only Ergo config from the pinned upstream default."""
from pathlib import Path
import re
import sys


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: make_config.py UPSTREAM_DEFAULT OUTPUT_YAML", file=sys.stderr)
        return 2
    source, destination = map(Path, sys.argv[1:])
    text = source.read_text(encoding="utf-8")
    text = text.replace("name: ErgoTest", "name: ErgoBench")
    text = text.replace("name: ergo.test", "name: ergo-bench.localnet")
    text, ipv6 = re.subn(
        r'(?m)^        "\[::1\]:6667":.*$',
        "        # IPv6 listener disabled for this IPv4-only profile",
        text,
        count=1,
    )
    text, tls = re.subn(
        r'(?m)^        ":6697":.*?^            min-tls-version: 1\.2\n',
        "",
        text,
        count=1,
        flags=re.DOTALL,
    )
    if ipv6 != 1 or tls != 1:
        raise SystemExit("could not remove upstream IPv6/TLS listeners")
    if '"127.0.0.1:6667":' not in text or '":6697":' in text:
        raise SystemExit("expected exactly the plaintext loopback listener")
    text, lang = re.subn(
        r"(?m)^    path: languages$",
        "    path: /opt/benchmark/languages",
        text,
        count=1,
    )
    if lang != 1:
        raise SystemExit("could not set the pinned language-data path")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
