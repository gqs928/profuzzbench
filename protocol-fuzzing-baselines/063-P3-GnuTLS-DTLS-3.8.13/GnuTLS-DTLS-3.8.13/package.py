#!/usr/bin/env python3
"""Verify completed GnuTLS evidence and create its standalone delivery ZIP."""
from __future__ import annotations
import hashlib, json, sys, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CAMPAIGN = ROOT / "results" / "gnutls-dtls-fuzz-30m-20261112"
DEST = ROOT.parent / "deliverables" / "12-protocol-baselines-2026-11-03-framework"
ZIP = DEST / "63-GnuTLS-DTLS-3.8.13.zip"
INCLUDE = [
    ".dockerignore", "ACCEPTANCE.md", "Dockerfile", "PACKAGE-MANIFEST.md",
    "README.md", "build.sh", "capture_seeds.py", "compose.yaml", "deadline_wrapper.py",
    "images.env", "package.py", "prepare-target.sh", "prepare_seeds.py",
    "protocol_smoke.py", "replay_queue.py", "run-benchmark.sh", "run.sh",
    "seeds-manifest.json", "source-lock.json", "verify_listener_closed.py",
    "build-logs", "seeds", "source", "results/campaign-console.log",
    "results/seed-compatibility", "results/gnutls-dtls-fuzz-30m-20261112",
]

def require(path: Path) -> None:
    if not path.is_file() or path.stat().st_size == 0:
        raise RuntimeError(f"required evidence missing or empty: {path.relative_to(ROOT)}")

def main() -> int:
    required = [ROOT / "ACCEPTANCE.md", ROOT / "PACKAGE-MANIFEST.md",
                ROOT / "README.md", ROOT / "source-lock.json",
                ROOT / "build-logs" / "build.log", ROOT / "build-logs" / "image-id.txt",
                CAMPAIGN / "fuzzer_stats", CAMPAIGN / "plot_data",
                CAMPAIGN / "run-parameters.txt", CAMPAIGN / "fuzzer-deadline.json",
                CAMPAIGN / "preflight-smoke.json",
                CAMPAIGN / "replay-validation" / "replay-summary.json",
                CAMPAIGN / "postrun-smoke.json",
                CAMPAIGN / "listener-closed.json"]
    for path in required:
        require(path)
    deadline = json.loads((CAMPAIGN / "fuzzer-deadline.json").read_text())
    if not deadline.get("deadline_reached") or deadline.get("stop_method") not in ("SIGINT", "SIGTERM"):
        raise RuntimeError(f"formal campaign did not reach its bounded deadline: {deadline}")
    smoke = json.loads((CAMPAIGN / "preflight-smoke.json").read_text())
    if not smoke.get("handshakes_complete"):
        raise RuntimeError(f"preflight DTLS handshake failed: {smoke}")
    after = json.loads((CAMPAIGN / "postrun-smoke.json").read_text())
    if not after.get("handshakes_complete"):
        raise RuntimeError(f"post-run DTLS smoke failed: {after}")
    closed = json.loads((CAMPAIGN / "listener-closed.json").read_text())
    if not closed.get("listener_closed"):
        raise RuntimeError(f"target listener/process was not stopped: {closed}")
    acceptance = (ROOT / "ACCEPTANCE.md").read_text(encoding="utf-8").lower()
    if "status: complete" not in acceptance:
        raise RuntimeError("ACCEPTANCE.md must record status: complete before packaging")
    DEST.mkdir(parents=True, exist_ok=True)
    if ZIP.exists():
        ZIP.unlink()
    files: set[Path] = set()
    for name in INCLUDE:
        path = ROOT / name
        if not path.exists():
            raise RuntimeError(f"declared package input missing: {name}")
        if path.is_file():
            files.add(path)
        else:
            files.update(p for p in path.rglob("*") if p.is_file())
    files = {p for p in files if "__pycache__" not in p.parts and p.suffix != ".pyc"}
    with zipfile.ZipFile(ZIP, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in sorted(files):
            archive.write(path, Path("GnuTLS-DTLS-3.8.13") / path.relative_to(ROOT))
    with zipfile.ZipFile(ZIP) as archive:
        bad = archive.testzip()
        if bad:
            raise RuntimeError(f"ZIP CRC check failed: {bad}")
        names = set(archive.namelist())
        if any("基准化经验库" in name for name in names):
            raise RuntimeError("shared experience library must not be included in protocol delivery")
    digest = hashlib.sha256(ZIP.read_bytes()).hexdigest()
    sidecar = ZIP.with_suffix(ZIP.suffix + ".sha256")
    sidecar.write_text(f"{digest}  {ZIP.name}\n", encoding="ascii")
    if hashlib.sha256(ZIP.read_bytes()).hexdigest() != digest:
        raise RuntimeError("ZIP SHA-256 post-write verification failed")
    print(f"PASS: {ZIP} ({ZIP.stat().st_size} bytes), SHA-256 {digest}")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, zipfile.BadZipFile) as exc:
        print(f"package validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
