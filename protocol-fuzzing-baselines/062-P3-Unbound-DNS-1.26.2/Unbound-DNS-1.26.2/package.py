#!/usr/bin/env python3
"""Verify the completed Unbound evidence and create its standalone delivery ZIP."""
from __future__ import annotations
import hashlib, json, sys, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CAMPAIGN = ROOT / "results" / "unbound-fuzz-30m-20261112"
DEST = ROOT.parent / "deliverables" / "12-protocol-baselines-2026-11-03-framework"
ZIP = DEST / "62-Unbound-DNS-1.26.2.zip"

def require(path: Path) -> None:
    if not path.is_file() or path.stat().st_size == 0:
        raise RuntimeError(f"required evidence missing or empty: {path.relative_to(ROOT)}")

def main() -> int:
    required = [ROOT / "ACCEPTANCE.md", ROOT / "PACKAGE-MANIFEST.md",
                ROOT / "README.md", ROOT / "source-lock.json",
                ROOT / "build-logs" / "build.log", ROOT / "build-logs" / "image-id.txt",
                CAMPAIGN / "fuzzer_stats", CAMPAIGN / "plot_data",
                CAMPAIGN / "run-parameters.txt", CAMPAIGN / "fuzzer-deadline.json",
                CAMPAIGN / "replay-validation" / "replay-summary.json",
                ROOT / "results" / "unbound-postrun-smoke-20261112" / "protocol-smoke.json",
                ROOT / "results" / "unbound-postrun-smoke-20261112" / "listener-closed.json"]
    for path in required:
        require(path)
    deadline = json.loads((CAMPAIGN / "fuzzer-deadline.json").read_text())
    if not deadline.get("deadline_reached") or deadline.get("stop_method") not in ("SIGINT", "SIGTERM"):
        raise RuntimeError(f"formal campaign did not reach its bounded deadline: {deadline}")
    smoke_dir = ROOT / "results" / "unbound-postrun-smoke-20261112"
    smoke = json.loads((smoke_dir / "protocol-smoke.json").read_text())
    if len(smoke.get("queries", [])) != 12:
        raise RuntimeError(f"post-run DNS/TCP smoke was not 12/12: {smoke}")
    closed = json.loads((smoke_dir / "listener-closed.json").read_text())
    if not closed.get("listener_closed"):
        raise RuntimeError(f"DNS/TCP listener was not stopped: {closed}")
    if "status: complete" not in (ROOT / "ACCEPTANCE.md").read_text(encoding="utf-8").lower():
        raise RuntimeError("ACCEPTANCE.md must record status: complete before packaging")
    DEST.mkdir(parents=True, exist_ok=True)
    if ZIP.exists():
        ZIP.unlink()
    with zipfile.ZipFile(ZIP, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in sorted(ROOT.rglob("*")):
            if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc":
                continue
            archive.write(path, Path("Unbound-DNS-1.26.2") / path.relative_to(ROOT))
    with zipfile.ZipFile(ZIP) as archive:
        bad = archive.testzip()
        if bad:
            raise RuntimeError(f"ZIP CRC check failed: {bad}")
        if any("基准化经验库" in name for name in archive.namelist()):
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
