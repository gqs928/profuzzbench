#!/usr/bin/env python3
"""Generate compact, deterministic FTP control-session seed files."""
import hashlib
import pathlib
import sys


SESSIONS = {
    "01-anonymous-basic": ["USER anonymous", "SYST", "FEAT", "PWD", "TYPE I", "NOOP", "QUIT"],
    "02-anonymous-path": ["USER ftp", "PWD", "CWD /", "CDUP", "PWD", "QUIT"],
    "03-anonymous-options": ["USER anonymous", "OPTS UTF8 ON", "MODE S", "STRU F", "TYPE A", "QUIT"],
    "04-prelogin": ["SYST", "FEAT", "NOOP", "HELP", "STAT", "QUIT"],
    "05-bad-user": ["USER invalid-user", "PASS fuzz", "USER anonymous", "QUIT"],
    "06-mixed-case": ["uSeR anonymous", "sYsT", "pWd", "nOoP", "qUiT"],
    "07-reset": ["USER anonymous", "REIN", "USER ftp", "PWD", "QUIT"],
    "08-command-arguments": ["USER anonymous", "ALLO 64", "SITE HELP", "SIZE missing.txt", "QUIT"],
    "09-repeated-noop": ["USER anonymous", "NOOP", "NOOP", "NOOP", "STAT", "QUIT"],
    "10-malformed-lines": ["USER anonymous", "XUNKNOWN value", "TYPE Z", "OPTS", "QUIT"],
}


def main():
    out = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "seeds")
    out.mkdir(parents=True, exist_ok=True)
    manifest = ["file\tbytes\tsha256\tcommands"]
    for name, commands in SESSIONS.items():
        payload = ("\r\n".join(commands) + "\r\n").encode("ascii")
        path = out / name
        path.write_bytes(payload)
        manifest.append(f"{path.name}\t{len(payload)}\t{hashlib.sha256(payload).hexdigest()}\t{len(commands)}")
    (out.parent / f"{out.name}-manifest.tsv").write_text("\n".join(manifest) + "\n")


if __name__ == "__main__":
    main()
