#!/usr/bin/env python3
"""Create the protocol-specific Knot DNS delivery and verify its contents."""
from __future__ import annotations

import hashlib
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parent
DELIVERY = ROOT.parent / "deliverables" / "12-protocol-baselines-2026-11-03-framework"
ARCHIVE = DELIVERY / "60-Knot-DNS-3.6.2.zip"
RESULT_ROOTS = {
    "results/knot-dns-preflight-r4-20261112",
    "results/knot-dns-fuzz-30m-20261112",
    "results/dns-tcp-smoke-post-20261112",
}
REQUIRED = {
    "README.md", "ACCEPTANCE.md", "source-lock.json", "source-checksums.sha256",
    "Dockerfile", "compose.yaml", "knot.conf", "fuzz.test.zone", "dns-tcp.dict",
    "source/knot-3.6.2.tar.xz", "source/knot-3.6.2.tar.xz.asc",
    "source/knot-keyblock.asc", "source/aflnet-dns-tcp.patch",
    "source/aflnet-network-config-terminator.patch",
    "source/dns-tcp-aflnet.inc", "source/dns-tcp-parser-test.c",
    "results/knot-dns-preflight-r4-20261112/fuzzer_stats",
    "results/knot-dns-preflight-r4-20261112/fuzzer-deadline.json",
    "results/knot-dns-fuzz-30m-20261112/fuzzer_stats",
    "results/knot-dns-fuzz-30m-20261112/fuzzer-deadline.json",
    "results/knot-dns-fuzz-30m-20261112/replay-validation/replay-summary.json",
    "results/dns-tcp-smoke-post-20261112/protocol-smoke.json",
    "results/dns-tcp-smoke-post-20261112/listener-closed.json",
    "post-smoke.sh", "verify_listener_closed.py",
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
    missing = sorted(rel for rel in REQUIRED if not (ROOT / rel).is_file())
    if missing:
        raise RuntimeError(f"required evidence missing: {missing}")
    files = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        relative = path.relative_to(ROOT).as_posix()
        if relative.startswith("results/") and not any(
                relative == root or relative.startswith(root + "/") for root in RESULT_ROOTS):
            continue
        if relative.endswith(".zip") or relative.endswith(".zip.sha256"):
            continue
        files.append(path)
    with ZipFile(ARCHIVE, "w", ZIP_DEFLATED, compresslevel=6) as bundle:
        for path in files:
            bundle.write(path, path.relative_to(ROOT).as_posix())
    with ZipFile(ARCHIVE) as bundle:
        if (bad := bundle.testzip()) is not None:
            raise RuntimeError(f"ZIP integrity failed: {bad}")
        names = set(bundle.namelist())
        if (missing := sorted(REQUIRED - names)):
            raise RuntimeError(f"archive missing required files: {missing}")
        if any(name.endswith("基准化经验库.md") for name in names):
            raise RuntimeError("shared framework experience stays in the central library")
        for line in bundle.read("source-checksums.sha256").decode("utf-8").splitlines():
            expected, rel = line.split("  ", 1)
            if hashlib.sha256(bundle.read(rel)).hexdigest() != expected:
                raise RuntimeError(f"source checksum mismatch: {rel}")
    digest = hashlib.sha256(ARCHIVE.read_bytes()).hexdigest()
    ARCHIVE.with_suffix(ARCHIVE.suffix + ".sha256").write_text(
        f"{digest}  {ARCHIVE.name}\n", encoding="utf-8")
    print(f"PASS: {ARCHIVE.name}, {len(files)} files, {ARCHIVE.stat().st_size} bytes, SHA256 {digest}")


if __name__ == "__main__":
    main()
