#!/usr/bin/env python3
"""Compare real FTP control sessions against reference and AFL/ASan targets."""
import argparse
import hashlib
import json
import pathlib
import socket
import subprocess
import time


def read_reply(reader):
    lines = []
    first = reader.readline()
    if not first:
        raise RuntimeError("server closed the control connection before replying")
    lines.append(first)
    if len(first) >= 4 and first[:3].isdigit() and first[3:4] == b"-":
        code = first[:3]
        while True:
            line = reader.readline()
            if not line:
                raise RuntimeError("server closed during a multiline reply")
            lines.append(line)
            if line.startswith(code + b" "):
                break
    return b"".join(lines)


def run_once(binary, config, log_path, expect_alive=False):
    with open(log_path, "ab") as log:
        server = subprocess.Popen([binary, config], stdout=log, stderr=log)
        try:
            deadline = time.monotonic() + 5
            connection = None
            while time.monotonic() < deadline:
                if server.poll() is not None:
                    raise RuntimeError(f"server exited during startup with {server.returncode}")
                try:
                    connection = socket.create_connection(("127.0.0.1", 2121), timeout=0.5)
                    break
                except OSError:
                    time.sleep(0.02)
            if connection is None:
                raise RuntimeError("FTP listener did not become ready")
            with connection:
                connection.settimeout(1.5)
                reader = connection.makefile("rb")
                transcript = [read_reply(reader)]
                for command in (b"USER anonymous\r\n", b"SYST\r\n", b"FEAT\r\n",
                                b"PWD\r\n", b"TYPE I\r\n", b"CWD /\r\n", b"CDUP\r\n",
                                b"NOOP\r\n", b"STAT\r\n", b"HELP\r\n", b"QUIT\r\n"):
                    connection.sendall(command)
                    transcript.append(command)
                    transcript.append(read_reply(reader))
                reader.close()
            if expect_alive:
                time.sleep(0.05)
                if server.poll() is not None:
                    raise RuntimeError(f"instrumented server exited after the QUIT reply ({server.returncode})")
            data = b"".join(transcript)
            codes = []
            for line in data.splitlines():
                if len(line) >= 3 and line[:3].isdigit():
                    codes.append(line[:3].decode("ascii"))
            return data, codes
        finally:
            if server.poll() is None:
                server.terminate()
            try:
                server.wait(timeout=3)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=3)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", required=True)
    parser.add_argument("--instrumented", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--log", required=True)
    parser.add_argument("--repetitions", type=int, default=3)
    args = parser.parse_args()
    report = {"protocol_scope": "FTP control over TCP/IPv4 loopback; passive/active data channels disabled",
              "repetitions": args.repetitions, "variants": {}}
    all_transcripts = {}
    for name, binary in (("reference", args.reference), ("AFL_ASan", args.instrumented)):
        runs = []
        for index in range(args.repetitions):
            transcript, codes = run_once(binary, args.config, args.log,
                                         expect_alive=name == "AFL_ASan")
            runs.append({"response_codes": codes,
                         "transcript_sha256": hashlib.sha256(transcript).hexdigest()})
            if index == 0:
                pathlib.Path(args.output).with_name(f"{name.lower()}-transcript.txt").write_bytes(transcript)
        report["variants"][name] = {"runs": runs,
                                    "stable_response_codes": len({tuple(r["response_codes"]) for r in runs}) == 1,
                                    "stable_transcript": len({r["transcript_sha256"] for r in runs}) == 1}
        all_transcripts[name] = runs[0]["response_codes"]
    report["reference_matches_instrumented_response_codes"] = all_transcripts["reference"] == all_transcripts["AFL_ASan"]
    report["pass"] = all(v["stable_response_codes"] for v in report["variants"].values()) and report["reference_matches_instrumented_response_codes"]
    pathlib.Path(args.output).write_text(json.dumps(report, indent=2) + "\n")
    if not report["pass"]:
        raise SystemExit("service smoke/reference parity failed; inspect the report and transcript files")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
