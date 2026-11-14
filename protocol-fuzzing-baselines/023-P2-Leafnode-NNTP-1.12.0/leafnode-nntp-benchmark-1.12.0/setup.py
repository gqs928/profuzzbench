#!/usr/bin/env python3
from pathlib import Path

for variant in ("reference", "afl", "gcov"):
    prefix = Path("/opt") / f"leafnode-{variant}"
    for name in ("etc", "spool", "run", "log"):
        (prefix / name).mkdir(parents=True, exist_ok=True)
    (prefix / "etc" / "config").write_text(
        "server = 127.0.0.1\n"
        "expire = 20\n"
        "fqdn = leafnode-benchmark-20261108.fuzzing-lab.net\n"
        "allowstrangers = 1\n",
        encoding="ascii",
    )
