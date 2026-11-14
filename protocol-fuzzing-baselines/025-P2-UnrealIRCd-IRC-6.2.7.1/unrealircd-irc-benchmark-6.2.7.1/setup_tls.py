#!/usr/bin/env python3
"""Install the final benchmark config and local certificate in each variant."""
from pathlib import Path
import os
import shutil
import sys


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: setup_tls.py PREFIX [PREFIX ...]", file=sys.stderr)
        return 2
    config = Path("/opt/benchmark/configs/unrealircd-tls.conf")
    source_cert = Path("/opt/benchmark/certs/server.cert.pem")
    source_key = Path("/opt/benchmark/certs/server.key.pem")
    for value in sys.argv[1:]:
        prefix = Path(value)
        conf = prefix / "conf"
        shutil.copy2(config, conf / "unrealircd.conf")
        tls_dir = conf / "tls"
        tls_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_cert, tls_dir / "server.cert.pem")
        shutil.copy2(source_key, tls_dir / "server.key.pem")
        os.chmod(tls_dir / "server.key.pem", 0o600)
        os.chmod(tls_dir / "server.cert.pem", 0o644)
        os.chown(tls_dir, 1000, 1000)
        for path in (tls_dir / "server.key.pem", tls_dir / "server.cert.pem"):
            os.chown(path, 1000, 1000)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
