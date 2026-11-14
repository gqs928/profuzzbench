#!/usr/bin/env python3
"""Pack and integrity-check the dcm4che protocol-specific delivery."""
from __future__ import annotations

import hashlib
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parent
DELIVERY = (ROOT.parent / "deliverables" /
            "12-protocol-baselines-2026-11-03-framework")
ARCHIVE = DELIVERY / "58-dcm4che-DICOM-5.35.2.zip"
RESULT_ROOTS = {
    "results/dcm4che-preflight-20261112",
    "results/dcm4che-fuzz-30m-20261112",
    "results/dicom-smoke-post-20261112",
}


def main() -> None:
    DELIVERY.mkdir(parents=True, exist_ok=True)
    files = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        relative = path.relative_to(ROOT).as_posix()
        if relative.startswith("results/") and not any(
                relative == root or relative.startswith(root + "/")
                for root in RESULT_ROOTS):
            continue
        files.append(path)
    with ZipFile(ARCHIVE, "w", ZIP_DEFLATED, compresslevel=6) as bundle:
        for path in files:
            bundle.write(path, path.relative_to(ROOT).as_posix())
    with ZipFile(ARCHIVE) as bundle:
        broken = bundle.testzip()
        if broken:
            raise RuntimeError(f"ZIP integrity failed: {broken}")
        names = set(bundle.namelist())
        required = {
            "README.md", "ACCEPTANCE.md", "source-lock.json", "dicom-parser-test.c",
            "aflnet-dicom.patch", "dicom_aflnet.inc", "prepare_seeds.py",
            "replay_queue.py", "dcm4che-5.35.2-bin.tar.gz",
            "results/dcm4che-preflight-20261112/fuzzer_stats",
            "results/dcm4che-preflight-20261112/fuzzer-deadline.json",
            "results/dcm4che-fuzz-30m-20261112/fuzzer_stats",
            "results/dcm4che-fuzz-30m-20261112/fuzzer-deadline.json",
            "results/dcm4che-fuzz-30m-20261112/replay-validation/replay-summary.json",
            "results/dicom-smoke-post-20261112/protocol-smoke.json",
            "results/dicom-smoke-post-20261112/listener-closed.json",
            "post-smoke.sh", "verify_listener_closed.py",
        }
        missing = sorted(required - names)
        if missing:
            raise RuntimeError(f"package missing required files: {missing}")
        if any(name.endswith("基准化经验库.md") for name in names):
            raise RuntimeError("shared automation experience belongs in the central library only")
    digest = hashlib.sha256(ARCHIVE.read_bytes()).hexdigest()
    ARCHIVE.with_suffix(ARCHIVE.suffix + ".sha256").write_text(
        f"{digest}  {ARCHIVE.name}\n", encoding="utf-8")
    print(f"PASS: {ARCHIVE.name}, {len(files)} files, {ARCHIVE.stat().st_size} bytes, SHA256 {digest}")


if __name__ == "__main__":
    main()
