#!/usr/bin/env python3
from pathlib import Path
import shutil
import sys

if len(sys.argv) < 2:
    raise SystemExit("usage: setup.py PREFIX [PREFIX ...]")
config = Path("/opt/benchmark/configs/unrealircd.conf")
for value in sys.argv[1:]:
    prefix = Path(value)
    (prefix / "conf").mkdir(parents=True, exist_ok=True)
    shutil.copy2(config, prefix / "conf" / "unrealircd.conf")
