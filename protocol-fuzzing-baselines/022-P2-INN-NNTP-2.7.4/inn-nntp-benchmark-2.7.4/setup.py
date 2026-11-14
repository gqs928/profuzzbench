#!/usr/bin/env python3
from pathlib import Path
import re

for variant in ("reference", "afl", "gcov"):
    prefix = Path("/opt") / f"inn-{variant}"
    etc = prefix / "etc"
    db = prefix / "db"
    spool = prefix / "spool"
    for d in (db, spool / "articles" / "comp" / "test", spool / "overview",
              prefix / "log", prefix / "run", prefix / "tmp"):
        d.mkdir(parents=True, exist_ok=True)
    conf = etc / "inn.conf"
    text = conf.read_text(errors="replace")
    overrides = {
        "pathhost": "nntp.test.invalid",
        "pathnews": str(prefix),
        "patharticles": str(spool / "articles"),
        "pathdb": str(db),
        "pathetc": str(etc),
        "pathlog": str(prefix / "log"),
        "pathoverview": str(spool / "overview"),
        "pathrun": str(prefix / "run"),
        "pathspool": str(spool),
        "pathtmp": str(prefix / "tmp"),
        "organization": '"Protocol fuzz benchmark"',
        "noreader": "false",
        "nnrpdoverstats": "false",
        "nnrpdloadlimit": "0",
        "maxconnections": "128",
    }
    for key, value in overrides.items():
        pattern = rf"(?m)^{re.escape(key)}:\s*.*$"
        replacement = f"{key}: {value}"
        if re.search(pattern, text):
            text = re.sub(pattern, lambda _m, r=replacement: r, text, count=1)
        else:
            text += f"\n{replacement}\n"
    conf.write_text(text)
    (etc / "readers.conf").write_text(
        'auth "local" {\n    hosts: "127.0.0.1, localhost, ::1, stdin"\n'
        '    default: "<local>"\n}\n\n'
        'access "read-only" {\n    users: "<local>"\n'
        '    newsgroups: "*"\n    access: R\n}\n', encoding="ascii")
    (db / "active").write_text(
        "comp.test 2 1 y\ncontrol 1 1 y\ncontrol.cancel 1 1 y\njunk 1 1 y\n",
        encoding="ascii")
    (db / "newsgroups").write_text(
        "comp.test Deterministic NNTP benchmark group\n"
        "control Control messages\ncontrol.cancel Cancel messages\njunk Junk articles\n",
        encoding="ascii")
    (db / "active.times").write_text("", encoding="ascii")
