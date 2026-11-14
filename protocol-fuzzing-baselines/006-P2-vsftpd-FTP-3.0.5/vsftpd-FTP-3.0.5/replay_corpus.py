#!/usr/bin/env python3
"""Replay FTP command-sequence samples against a fresh vsftpd per sample."""
import argparse
import json
import pathlib
import socket
import subprocess
import time


def read_reply(reader):
    first = reader.readline()
    if not first:
        return b""
    lines = [first]
    if len(first) >= 4 and first[:3].isdigit() and first[3:4] == b"-":
        code = first[:3]
        while True:
            line = reader.readline()
            if not line:
                break
            lines.append(line)
            if line.startswith(code + b" "):
                break
    return b"".join(lines)


def connect_until_ready(proc, timeout):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(f"server exited during startup ({proc.returncode})")
        try:
            return socket.create_connection(("127.0.0.1", 2121), timeout=0.25)
        except OSError:
            time.sleep(0.01)
    raise TimeoutError("FTP listener did not become ready")


def replay(binary, config, payload, timeout, log):
    server = subprocess.Popen([binary, config], stdout=log, stderr=log)
    started = time.monotonic()
    replies = []
    response_texts = []
    status = "ok"
    error = None
    reader = None
    target_alive_at_timeout = None
    try:
        with connect_until_ready(server, timeout) as conn:
            conn.settimeout(timeout)
            reader = conn.makefile("rb")
            try:
                greeting = read_reply(reader)
                response_texts.append(greeting.decode("utf-8", errors="replace"))
                replies.extend(line[:3].decode("ascii", errors="replace")
                               for line in greeting.splitlines()
                               if len(line) >= 3 and line[:3].isdigit())
                if payload:
                    parts = payload.split(b"\r\n")
                    commands = [part + b"\r\n" for part in parts[:-1]]
                    if parts[-1]:
                        commands.append(parts[-1])
                else:
                    commands = []
                for command in commands:
                    if not command:
                        continue
                    conn.sendall(command)
                    response = read_reply(reader)
                    if not response:
                        status = "no_response_or_closed"
                        break
                    response_texts.append(response.decode("utf-8", errors="replace"))
                    replies.extend(line[:3].decode("ascii", errors="replace")
                                   for line in response.splitlines()
                                   if len(line) >= 3 and line[:3].isdigit())
            except TimeoutError:
                target_alive_at_timeout = server.poll() is None
                raise
            reader.close()
            reader = None
    except (OSError, TimeoutError, RuntimeError) as exc:
        status = "response_timeout" if isinstance(exc, TimeoutError) else "replay_error"
        error = f"{type(exc).__name__}: {exc}"
    finally:
        if reader is not None:
            reader.close()
        if server.poll() is None:
            try:
                server.wait(timeout=1)
            except subprocess.TimeoutExpired:
                server.terminate()
                try:
                    server.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    server.kill()
                    server.wait(timeout=2)
    return {"status": status, "response_codes": replies,
            "responses": response_texts,
            "server_exit_code": server.returncode,
            "target_alive_at_timeout": target_alive_at_timeout,
            "elapsed_seconds": round(time.monotonic() - started, 4),
            "error": error}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--corpus", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--log", required=True)
    parser.add_argument("--timeout", type=float, default=1.0)
    args = parser.parse_args()
    corpus = pathlib.Path(args.corpus)
    files = sorted(path for path in corpus.iterdir() if path.is_file())
    if not files:
        raise SystemExit(f"no replayable inputs found in {corpus}")
    output = pathlib.Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.log, "ab") as log, open(output, "w") as results:
        for path in files:
            result = replay(args.binary, args.config, path.read_bytes(), args.timeout, log)
            result["sample"] = path.name
            results.write(json.dumps(result, sort_keys=True) + "\n")
    print(f"replayed {len(files)} samples; outcomes={output}")


if __name__ == "__main__":
    main()
