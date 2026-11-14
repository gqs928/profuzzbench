#!/usr/bin/env python3
from pathlib import Path
import json
import os
import re
import signal
import socket
import subprocess
import sys
import time

PORT = 1119

class NNTP:
    def __init__(self, sock):
        self.sock = sock
        self.file = sock.makefile("rb")
        self.lines = []
    def line(self):
        data = self.file.readline()
        if not data:
            raise RuntimeError("NNTP connection closed while reading a response")
        self.lines.append(data)
        return data.rstrip(b"\r\n")
    def send(self, command):
        self.sock.sendall(command.encode("ascii") + b"\r\n")
        line = self.line()
        if not re.match(rb"^[1-5][0-9]{2}[ -]", line):
            raise RuntimeError(f"invalid NNTP status line: {line!r}")
        code = int(line[:3])
        if line[3:4] == b"-" or code in (100, 101, 215, 220, 221, 222, 224, 230, 231, 282):
            while self.line() != b".":
                pass
        return code

def exercise(variant, out):
    prefix = Path("/opt") / f"inn-{variant}"
    logpath = out / f"{variant}.server.log"
    log = logpath.open("wb")
    proc = subprocess.Popen([str(prefix / "bin/nnrpd"), "-D", "-f", "-4", "127.0.0.1",
                            "-p", str(PORT), "-n"],
                            stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    client = None
    try:
        deadline = time.monotonic() + 12
        while True:
            if proc.poll() is not None:
                raise RuntimeError(f"{variant} nnrpd exited {proc.returncode}; see {logpath}")
            try:
                client = NNTP(socket.create_connection(("127.0.0.1", PORT), timeout=3))
                break
            except OSError:
                if time.monotonic() >= deadline:
                    raise RuntimeError(f"{variant} nnrpd did not listen on {PORT}; see {logpath}")
                time.sleep(0.1)
        greeting = client.line()
        if not greeting[:3] in (b"200", b"201"):
            raise RuntimeError(f"unexpected greeting: {greeting!r}")
        codes = [client.send("CAPABILITIES"), client.send("MODE READER"),
                 client.send("DATE"), client.send("LIST ACTIVE"),
                 client.send("GROUP comp.test"), client.send("STAT 1"),
                 client.send("HELP"), client.send("QUIT")]
        raw = b"".join(client.lines)
        transcript = out / f"{variant}.transcript.bin"
        transcript.write_bytes(raw)
        expected = (101, 201, 111, 215, 211, 423, 100, 205)
        if tuple(codes) != expected:
            raise RuntimeError(f"{variant} status mismatch: {codes}, expected {expected}; see {logpath}")
        return {"variant": variant, "codes": codes, "transcript": str(transcript)}
    finally:
        if client:
            client.sock.close()
            client.file.close()
        if proc.poll() is None:
            os.killpg(proc.pid, signal.SIGTERM)
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait(timeout=5)
        log.close()

def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: protocol_smoke.py OUTPUT_DIR")
    out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
    reports = [exercise(v, out) for v in ("reference", "afl", "gcov")]
    if len({tuple(x["codes"]) for x in reports}) != 1:
        raise SystemExit("reference/AFL/gcov NNTP status transcripts differ")
    (out / "summary.json").write_text(json.dumps(reports, indent=2) + "\n")
    print("PASS: reference, AFL, and gcov INN nnrpd variants handle reader commands identically")
    print("status_codes=" + ",".join(map(str, reports[0]["codes"])))

if __name__ == "__main__": main()
