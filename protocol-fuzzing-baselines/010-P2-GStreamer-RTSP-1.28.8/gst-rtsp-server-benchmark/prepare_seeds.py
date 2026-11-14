#!/usr/bin/env python3
import argparse
from pathlib import Path


def request(method: str, uri: str, cseq: int, headers: list[str] | None = None) -> bytes:
    lines = [f"{method} {uri} RTSP/1.0", f"CSeq: {cseq}", "User-Agent: gst-rtsp-baseline/1.0"]
    lines.extend(headers or [])
    return ("\r\n".join(lines) + "\r\n\r\n").encode("ascii")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("outdir", nargs="?", default="seeds")
    args = parser.parse_args()
    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    url = "rtsp://127.0.0.1:8554/test"
    options = request("OPTIONS", url, 1)
    describe = request("DESCRIBE", url, 2, ["Accept: application/sdp"])
    setup = request("SETUP", url + "/stream=0", 3,
                    ["Transport: RTP/AVP/TCP;unicast;interleaved=0-1"])
    seeds = {
        "options": options,
        "describe": options + describe,
        "setup": options + describe + setup,
        "unknown-method": request("FROB", url, 1),
        "unknown-path": request("OPTIONS", "rtsp://127.0.0.1:8554/missing", 1),
        "bad-cseq": (b"OPTIONS " + url.encode() + b" RTSP/1.0\r\nCSeq: nope\r\n\r\n"),
    }
    for name, data in seeds.items():
        (out / name).write_bytes(data)


if __name__ == "__main__":
    main()
