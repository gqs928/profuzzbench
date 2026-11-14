#!/usr/bin/env python3
"""Derive a loopback-only smoke configuration from the upstream example."""
from pathlib import Path
import re
import string
import sys


def make_config(source: Path, destination: Path) -> None:
    text = source.read_text(encoding="utf-8")
    text = text.replace('name "irc.example.org";', 'name "irc-bench.localnet";')
    text = text.replace('info "ExampleNET Server";', 'info "UnrealIRCd benchmark";')
    text = text.replace('"ExampleNET"', '"BenchmarkNet"')
    text = text.replace('"irc.example.org"', '"irc-bench.localnet"')
    text = text.replace('"services.example.org"', '"services-bench.localnet"')
    text = text.replace('"stats.example.org"', '"stats-bench.localnet"')
    text = text.replace("'set.this.to.email.address'", "'bench@example.invalid'")
    listen = re.compile(r"listen\s*\{\s*ip \*;\s*port 6667;\s*\}", re.MULTILINE)
    text, count = listen.subn(
        "listen {\n\tip 127.0.0.1;\n\tport 6667;\n}", text, count=1)
    if count != 1:
        raise SystemExit("could not isolate upstream example's plaintext IRC listener")
    text, count = re.subn(
        r"/\* Standard IRC SSL/TLS port 6697 \*/.*?/\* NOTE:",
        "/* NOTE:", text, count=1, flags=re.DOTALL)
    if count != 1:
        raise SystemExit("could not remove TLS/server-only listen blocks")
    alphabet = string.ascii_letters + string.digits
    keys = ["".join(alphabet[(i * 17 + offset) % len(alphabet)] for i in range(96))
            for offset in (0, 7, 19)]
    cloak = "cloak-keys {\n" + "".join(f'\t"{key}";\n' for key in keys) + "\t}"
    text, count = re.subn(r"cloak-keys\s*\{.*?\}", cloak, text,
                          count=1, flags=re.DOTALL)
    if count != 1:
        raise SystemExit("could not replace upstream cloak key placeholders")
    text, _ = re.subn(r"\noper bobsmith\s*\{.*?\n\}", "", text,
                      count=1, flags=re.DOTALL)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(text, encoding="utf-8")


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: make_config.py UPSTREAM_EXAMPLE OUTPUT_CONF")
    make_config(Path(sys.argv[1]), Path(sys.argv[2]))


if __name__ == "__main__":
    main()
