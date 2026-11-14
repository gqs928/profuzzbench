#!/usr/bin/env python3
"""Replay DTLS record sequences from AFLNet raw and KL-framed queues."""
from __future__ import annotations
import hashlib, json, os, signal, socket, struct, subprocess, sys, time
from collections import Counter
from pathlib import Path

SERVER = "/opt/gnutls/bin/gnutls-serv"
PORT = int(os.environ.get("GNUTLS_PORT", "20220"))
CERT_DIR = os.environ.get("GNUTLS_CERT_DIR", "/run/gnutls-benchmark")
PRIORITY = "NORMAL:-VERS-ALL:+VERS-DTLS1.2"
MAX_SAMPLE = 4 * 1024 * 1024

def split_records(data: bytes) -> list[bytes]:
    rows, offset = [], 0
    while offset < len(data):
        if len(data) - offset < 13:
            raise ValueError(f"truncated record header at offset {offset}")
        if data[offset + 1:offset + 3] != b"\xfe\xfd":
            raise ValueError(f"non-DTLS-1.2 version at offset {offset}")
        length = int.from_bytes(data[offset + 11:offset + 13], "big")
        end = offset + 13 + length
        if end > len(data):
            raise ValueError(f"record at {offset} exceeds sample length")
        rows.append(data[offset:end])
        offset = end
    return rows

def kl_records(data: bytes) -> list[bytes]:
    out, offset = [], 0
    while offset < len(data):
        if len(data) - offset < 4:
            raise ValueError("truncated KL frame length")
        size = struct.unpack_from("<I", data, offset)[0]
        offset += 4
        if size < 13 or size > 65507 or size > len(data) - offset:
            raise ValueError(f"invalid KL frame length {size}")
        out.extend(split_records(data[offset:offset + size]))
        offset += size
    return out

def bound() -> bool:
    result = subprocess.run(["ss", "-lunH"], capture_output=True, text=True, check=False)
    # Headerless `ss -lunH` output uses: Netid, Recv-Q, Send-Q,
    # Local Address:Port, Peer Address:Port. Match the local endpoint
    # (index 3), never the peer column (index 4).
    return any(len(f := line.split()) >= 4 and f[3].endswith(f":{PORT}")
               for line in result.stdout.splitlines())

def server_args() -> list[str]:
    return [SERVER, "--udp", "--nocookie", f"--port={PORT}", "--echo",
            f"--priority={PRIORITY}", f"--x509keyfile={CERT_DIR}/server.key",
            f"--x509certfile={CERT_DIR}/server.crt"]

def replay_one(path: Path, mode: str, outdir: Path, index: int) -> dict[str, object]:
    raw = path.read_bytes()
    row: dict[str, object] = {"sample": path.name, "mode": mode,
                              "input_bytes": len(raw), "ready": False,
                              "packets_sent": 0, "response_packets": 0,
                              "response_states": [], "events": []}
    if len(raw) > MAX_SAMPLE:
        row["events"].append("oversize_sample")
        return row
    try:
        packets = split_records(raw) if mode == "raw" else kl_records(raw)
        if not packets:
            raise ValueError("no DTLS records")
    except ValueError as exc:
        row["events"].append(f"parse_error:{exc}")
        return row
    log_path = outdir / f"{index:05d}-{mode}-{path.name}.log"
    with log_path.open("wb") as log:
        proc = subprocess.Popen(server_args(), stdout=log, stderr=subprocess.STDOUT,
                                start_new_session=True)
        try:
            deadline = time.monotonic() + 8
            while time.monotonic() < deadline and not bound():
                if proc.poll() is not None:
                    row["events"].append(f"target_exited:{proc.returncode}")
                    break
                time.sleep(0.05)
            row["ready"] = bound() and proc.poll() is None
            if not row["ready"]:
                return row
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client:
                client.connect(("127.0.0.1", PORT))
                for packet in packets:
                    client.send(packet)
                    row["packets_sent"] += 1
                    # The target and crypto work are local, but a 40 ms single
                    # recv timeout can still miss DTLS responses under load.
                    # Wait up to 250 ms for the first response, then keep
                    # collecting until 150 ms of quiet after the latest one.
                    quiet_deadline = time.monotonic() + 0.25
                    while time.monotonic() < quiet_deadline:
                        remaining = quiet_deadline - time.monotonic()
                        client.settimeout(min(0.05, max(0.001, remaining)))
                        try:
                            response = client.recv(65535)
                        except socket.timeout:
                            continue
                        row["response_packets"] += 1
                        offset = 0
                        while offset + 13 <= len(response):
                            ctype = response[offset]
                            version = int.from_bytes(response[offset + 1:offset + 3], "big")
                            length = int.from_bytes(response[offset + 11:offset + 13], "big")
                            if offset + 13 + length > len(response):
                                break
                            handshake = response[offset + 13] if ctype == 22 and length else None
                            row["response_states"].append({"content_type": ctype,
                                "version": version, "handshake_type": handshake})
                            offset += 13 + length
                        quiet_deadline = time.monotonic() + 0.15
                    time.sleep(0.03)
            row["target_alive_after_sample"] = proc.poll() is None
            if not row["target_alive_after_sample"]:
                row["events"].append(f"target_exited:{proc.returncode}")
        except OSError as exc:
            row["events"].append(f"transport_error:{exc}")
        finally:
            if proc.poll() is None:
                try:
                    os.killpg(proc.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                try:
                    proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    try:
                        os.killpg(proc.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    proc.wait()
    row["log"] = log_path.name
    row["input_sha256"] = hashlib.sha256(raw).hexdigest()
    return row

def main() -> int:
    if len(sys.argv) not in (3, 4):
        print("usage: replay_queue.py CAMPAIGN_DIR OUTDIR [MAX_PER_DIRECTORY]", file=sys.stderr)
        return 2
    campaign, outdir = Path(sys.argv[1]), Path(sys.argv[2])
    maximum = int(sys.argv[3]) if len(sys.argv) == 4 else 100
    if not 1 <= maximum <= 5000:
        raise ValueError("MAX_PER_DIRECTORY must be in [1, 5000]")
    outdir.mkdir(parents=True, exist_ok=True)
    if any(outdir.iterdir()):
        raise RuntimeError(f"output directory must be empty: {outdir}")
    subprocess.run(["/bin/bash", "/opt/benchmark/prepare-target.sh"], check=True,
                   capture_output=True, text=True, timeout=10)
    rows, index = [], 0
    for directory, mode in (("queue", "raw"), ("replayable-queue", "kl"),
                            ("replayable-new-ipsm-paths", "kl")):
        source = campaign / directory
        samples = sorted(p for p in source.iterdir() if p.is_file() and p.name.startswith("id:")) if source.is_dir() else []
        for sample in samples[:maximum]:
            index += 1
            rows.append(replay_one(sample, mode, outdir, index))
    event_counts = Counter(event.split(":", 1)[0] for row in rows for event in row["events"])
    report = {"target": "GnuTLS 3.8.13 gnutls-serv", "protocol": "DTLS 1.2/UDP",
              "directories": ["queue (raw DTLS record streams)",
                             "replayable-queue (KL little-endian frame lengths)",
                             "replayable-new-ipsm-paths (KL little-endian frame lengths)"],
              "samples": len(rows), "ready_samples": sum(bool(r["ready"]) for r in rows),
              "target_alive_after_samples": sum(bool(r.get("target_alive_after_sample")) for r in rows),
              "response_packets": sum(int(r["response_packets"]) for r in rows),
              "response_states": sum(len(r["response_states"]) for r in rows),
              "event_counts": dict(event_counts), "rows": rows}
    excluded = event_counts.get("parse_error", 0) + event_counts.get("oversize_sample", 0)
    eligible = len(rows) - excluded
    unexpected_events = set(event_counts) - {"parse_error", "oversize_sample"}
    report["eligible_samples"] = eligible
    report["unparsed_samples"] = event_counts.get("parse_error", 0)
    report["oversize_samples"] = event_counts.get("oversize_sample", 0)
    passed = (report["ready_samples"] == eligible
              and report["target_alive_after_samples"] == report["ready_samples"]
              and not unexpected_events)
    report["validation_passed"] = passed
    (outdir / "replay-summary.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Replay complete: {report['ready_samples']}/{eligible} parseable samples ready "
          f"({len(rows)} total, {excluded} excluded before target); "
          f"{report['response_packets']} response datagrams; events={dict(event_counts)}; "
          f"validation_passed={passed}")
    return 0 if passed else 1

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, subprocess.TimeoutExpired, ValueError) as exc:
        print(f"replay validation failed: {exc}", file=sys.stderr)
        raise SystemExit(2)
