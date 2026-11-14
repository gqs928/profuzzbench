#!/usr/bin/env python3
"""Verify OpenSSL DTLS campaign evidence and build its standalone delivery ZIP."""
from __future__ import annotations
import hashlib, json, sys, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CAMPAIGN = ROOT / "results" / "openssl-dtls-fuzz-30m-20261112"
DEST = ROOT.parent / "deliverables" / "12-protocol-baselines-2026-11-03-framework"
ZIP = DEST / "64-OpenSSL-DTLS-4.1.0.zip"
INCLUDE = [
    "ACCEPTANCE.md", "Dockerfile", "PACKAGE-MANIFEST.md",
    "README.md", "build.sh", "capture_seeds.py", "compose.yaml", "deadline_wrapper.py",
    "dtls_echo_server.c", "images.env", "package.py", "prepare-target.sh",
    "prepare_seeds.py", "protocol_smoke.py", "replay_queue.py", "run-benchmark.sh",
    "run.sh", "source-lock.json", "verify_listener_closed.py", "build-logs", "seeds",
    "source", "results/campaign-console.log",
    "results/campaign-console-previous-echo-failure-20261112.log",
    "results/openssl-dtls-preflight-echo-fix-20261112",
    "results/openssl-dtls-fuzz-30m-20261112",
]

def require(path: Path) -> None:
    if not path.is_file() or path.stat().st_size == 0:
        raise RuntimeError(f"required evidence missing or empty: {path.relative_to(ROOT)}")

def read_json(path: Path) -> dict:
    require(path)
    return json.loads(path.read_text(encoding="utf-8"))

def parse_stats(path: Path) -> dict[str, str]:
    require(path)
    result = {}
    for line in path.read_text(errors="replace").splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            result[key.strip()] = value.strip()
    return result

def main() -> int:
    for path in [ROOT / "ACCEPTANCE.md", ROOT / "PACKAGE-MANIFEST.md", ROOT / "README.md",
                 ROOT / "source-lock.json", ROOT / "build-logs/build.log",
                 ROOT / "build-logs/image-id.txt", ROOT / "source/openssl-4.1.0.tar.gz",
                 CAMPAIGN / "fuzzer_stats", CAMPAIGN / "plot_data", CAMPAIGN / "run-parameters.txt",
                 CAMPAIGN / "fuzzer-deadline.json", CAMPAIGN / "preflight-smoke.json",
                 CAMPAIGN / "replay-validation/replay-summary.json", CAMPAIGN / "postrun-smoke.json",
                 CAMPAIGN / "listener-closed.json"]:
        require(path)
    lock = json.loads((ROOT / "source-lock.json").read_text(encoding="utf-8"))
    source_hash = hashlib.sha256((ROOT / lock["target"]["source_archive"]).read_bytes()).hexdigest()
    if source_hash != lock["target"]["source_sha256"]:
        raise RuntimeError("OpenSSL source archive SHA-256 mismatch")
    deadline = read_json(CAMPAIGN / "fuzzer-deadline.json")
    if not deadline.get("deadline_reached") or deadline.get("stop_method") not in ("SIGINT", "SIGTERM"):
        raise RuntimeError(f"campaign did not reach bounded deadline: {deadline}")
    stats = parse_stats(CAMPAIGN / "fuzzer_stats")
    runtime = int(stats.get("last_update", "0")) - int(stats.get("start_time", "0"))
    # AFLNet's final stats refresh may be timestamped one second after SIGINT;
    # the deadline wrapper separately proves that the requested 1,800s limit fired.
    if runtime not in (1800, 1801):
        raise RuntimeError(f"formal AFLNet stats span is outside the 1,800s deadline window: {runtime}")
    for name in ("preflight-smoke.json", "postrun-smoke.json"):
        smoke = read_json(CAMPAIGN / name)
        if smoke.get("passes") != 3 or not smoke.get("handshakes_complete") or not smoke.get("reverse_echoes_received"):
            raise RuntimeError(f"DTLS handshake/reverse-echo smoke failed: {name}: {smoke}")
    replay = read_json(CAMPAIGN / "replay-validation/replay-summary.json")
    if not replay.get("validation_passed"):
        raise RuntimeError(f"queue replay validation failed: {replay}")
    closed = read_json(CAMPAIGN / "listener-closed.json")
    if not closed.get("listener_closed"):
        raise RuntimeError(f"target listener/process was not stopped: {closed}")
    if "status: complete" not in (ROOT / "ACCEPTANCE.md").read_text(encoding="utf-8").lower():
        raise RuntimeError("ACCEPTANCE.md must say status: complete before packaging")
    DEST.mkdir(parents=True, exist_ok=True)
    if ZIP.exists(): ZIP.unlink()
    files: set[Path] = set()
    for name in INCLUDE:
        path = ROOT / name
        if not path.exists():
            raise RuntimeError(f"declared package input missing: {name}")
        if path.is_file(): files.add(path)
        else: files.update(p for p in path.rglob("*") if p.is_file())
    files = {p for p in files if "__pycache__" not in p.parts and p.suffix != ".pyc"
             and "replay-validation-attempt-01" not in p.parts}
    with zipfile.ZipFile(ZIP, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in sorted(files):
            archive.write(path, Path("OpenSSL-DTLS-4.1.0") / path.relative_to(ROOT))
    with zipfile.ZipFile(ZIP) as archive:
        bad = archive.testzip()
        if bad: raise RuntimeError(f"ZIP CRC check failed: {bad}")
        if any("基准化经验库" in name for name in archive.namelist()):
            raise RuntimeError("central automation experience library must not be in protocol ZIP")
    digest = hashlib.sha256(ZIP.read_bytes()).hexdigest()
    sidecar = ZIP.with_suffix(ZIP.suffix + ".sha256")
    sidecar.write_text(f"{digest}  {ZIP.name}\n", encoding="ascii")
    if hashlib.sha256(ZIP.read_bytes()).hexdigest() != digest:
        raise RuntimeError("post-write SHA-256 verification failed")
    print(f"PASS: {ZIP} ({ZIP.stat().st_size} bytes), SHA-256 {digest}")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, zipfile.BadZipFile, KeyError) as exc:
        print(f"package validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
