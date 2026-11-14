#!/usr/bin/env python3
"""Pack and integrity-check the protocol-specific pynetdicom delivery."""
from __future__ import annotations

import hashlib
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parent
DELIVERY = ROOT.parent / "deliverables" / "12-protocol-baselines-2026-11-03-framework"
ARCHIVE = DELIVERY / "59-pynetdicom-DICOM-3.0.4.zip"
RESULT_ROOTS = {
    "results/pynetdicom-preflight-r2-20261112",
    "results/pynetdicom-fuzz-30m-20261112",
    "results/dicom-smoke-post-20261112",
}


def main() -> None:
    DELIVERY.mkdir(parents=True, exist_ok=True)
    checksum_path = ROOT / "source-checksums.sha256"
    source_files = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        relative = path.relative_to(ROOT).as_posix()
        if (relative == "source-checksums.sha256" or relative.startswith(("results/", "build-logs/"))
                or relative.endswith(".zip") or relative.endswith(".zip.sha256")):
            continue
        source_files.append(path)
    checksum_path.write_text("".join(
        f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(ROOT).as_posix()}\n"
        for path in source_files
    ), encoding="utf-8")
    files = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        relative = path.relative_to(ROOT).as_posix()
        if relative.startswith("results/") and not any(
            relative == root or relative.startswith(root + "/") for root in RESULT_ROOTS
        ):
            continue
        files.append(path)
    with ZipFile(ARCHIVE, "w", ZIP_DEFLATED, compresslevel=6) as bundle:
        for path in files:
            bundle.write(path, path.relative_to(ROOT).as_posix())
    with ZipFile(ARCHIVE) as bundle:
        if (bad := bundle.testzip()) is not None:
            raise RuntimeError(f"ZIP integrity failed: {bad}")
        names = set(bundle.namelist())
        required = {
            "README.md", "ACCEPTANCE.md", "source-lock.json", "source-checksums.sha256",
            "requirements.lock", "dicom-parser-test.c", "aflnet-dicom.patch",
            "dicom_aflnet.inc", "prepare_seeds.py", "replay_queue.py",
            "results/pynetdicom-fuzz-30m-20261112/fuzzer_stats",
            "results/pynetdicom-fuzz-30m-20261112/fuzzer-deadline.json",
            "results/pynetdicom-preflight-r2-20261112/fuzzer_stats",
            "results/pynetdicom-preflight-r2-20261112/fuzzer-deadline.json",
            "results/pynetdicom-fuzz-30m-20261112/replay-validation/replay-summary.json",
            "results/dicom-smoke-post-20261112/protocol-smoke.json",
            "results/dicom-smoke-post-20261112/listener-closed.json",
            "post-smoke.sh", "verify_listener_closed.py",
            "build-logs/image-cleanup.txt",
        }
        missing = sorted(required - names)
        if missing:
            raise RuntimeError(f"package missing required files: {missing}")
        if any(name.endswith("基准化经验库.md") for name in names):
            raise RuntimeError("shared automation experience belongs in the central library only")
        checksums = bundle.read("source-checksums.sha256").decode("utf-8").splitlines()
        for line in checksums:
            expected, rel = line.split("  ", 1)
            if hashlib.sha256(bundle.read(rel)).hexdigest() != expected:
                raise RuntimeError(f"source checksum mismatch: {rel}")
    digest = hashlib.sha256(ARCHIVE.read_bytes()).hexdigest()
    ARCHIVE.with_suffix(ARCHIVE.suffix + ".sha256").write_text(
        f"{digest}  {ARCHIVE.name}\n", encoding="utf-8"
    )
    print(f"PASS: {ARCHIVE.name}, {len(files)} files, {ARCHIVE.stat().st_size} bytes, SHA256 {digest}")


if __name__ == "__main__":
    main()
