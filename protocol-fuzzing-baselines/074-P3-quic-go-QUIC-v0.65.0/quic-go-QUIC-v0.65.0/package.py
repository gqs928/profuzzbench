#!/usr/bin/env python3
"""Validate Go native-fuzz evidence and create a standalone protocol ZIP."""
from __future__ import annotations

import hashlib
import json
import re
import sys
import zipfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEST = ROOT.parent / "deliverables/12-protocol-baselines-2026-11-03-framework"
PREFLIGHT = ROOT / "results/quic-go-preflight-60s-20261113"
CAMPAIGN = ROOT / "results/quic-go-fuzz-30m-20261113"
IMAGE = "quic-go-native-fuzz-bench:v0.65.0"
FINAL_ZIP = DEST / "74-quic-go-QUIC-v0.65.0.zip"
CANDIDATE_ZIP = Path("/tmp/74-quic-go-QUIC-v0.65.0-precleanup.zip")
ROOT_NAME = "quic-go-QUIC-v0.65.0"


def load_json(path: Path) -> dict:
    if not path.is_file() or path.stat().st_size == 0:
        raise RuntimeError(f"required JSON evidence missing: {path.relative_to(ROOT)}")
    return json.loads(path.read_text(encoding="utf-8"))


def verify_hash(path: Path, expected: str) -> None:
    if not path.is_file():
        raise RuntimeError(f"locked file missing: {path.relative_to(ROOT)}")
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != expected:
        raise RuntimeError(f"locked SHA-256 mismatch: {path.relative_to(ROOT)}")


def parse_elapsed(line: str) -> int:
    match = re.search(r"elapsed:\s*((?:\d+h)?(?:\d+m)?(?:\d+s)?)", line)
    if not match or not match.group(1):
        raise RuntimeError(f"cannot parse elapsed time from Go fuzz progress line: {line}")
    total = 0
    for value, unit in re.findall(r"(\d+)([hms])", match.group(1)):
        total += int(value) * {"h": 3600, "m": 60, "s": 1}[unit]
    return total


def check_run(run: Path, *, formal: bool) -> dict:
    metrics = load_json(run / "metrics.json")
    duration = 1800 if formal else 60
    if metrics.get("backend") != "go test native fuzz":
        raise RuntimeError(f"unexpected fuzz backend: {run.relative_to(ROOT)}")
    if metrics.get("fuzzer_exit_status") != 0 or metrics.get("panic_or_failure_markers"):
        raise RuntimeError(f"Go fuzz run failed or reported panic/failure: {run.relative_to(ROOT)}")
    if not metrics.get("final_progress_line") or int(metrics.get("final_execs") or 0) <= 0:
        raise RuntimeError(f"Go fuzz progress is missing or empty: {run.relative_to(ROOT)}")
    elapsed = parse_elapsed(metrics["final_progress_line"])
    if formal and elapsed < duration:
        raise RuntimeError(f"formal Go fuzz time was shorter than {duration}s: {elapsed}s")
    if not formal and not 55 <= elapsed <= 70:
        raise RuntimeError(f"preflight Go fuzz time outside 55-70s: {elapsed}s")
    if not (run / "run.log").is_file() or not (run / "run-times.txt").is_file():
        raise RuntimeError(f"Go fuzz run log or timestamps missing: {run.relative_to(ROOT)}")
    log_text = (run / "run.log").read_text(errors="replace")
    if not re.search(r"(?m)^ok\s+\S+\s+", log_text):
        raise RuntimeError(f"Go test log lacks a successful package result: {run.relative_to(ROOT)}")
    if (run / ".gocache").exists():
        raise RuntimeError(f"transient Go cache was not removed: {run.relative_to(ROOT)}")
    return metrics


def verify_times(run: Path, *, minimum_seconds: int) -> None:
    values = {}
    for line in (run / "run-times.txt").read_text().splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            values[key] = value
    start = datetime.fromisoformat(values["start_utc"].replace("Z", "+00:00"))
    end = datetime.fromisoformat(values["end_utc"].replace("Z", "+00:00"))
    elapsed = (end - start).total_seconds()
    if elapsed < minimum_seconds:
        raise RuntimeError(f"run timestamp span too short: {run.relative_to(ROOT)} ({elapsed}s)")


def collect_files() -> list[Path]:
    explicit = {
        ".dockerignore", "ACCEPTANCE.md", "Dockerfile", "PACKAGE-MANIFEST.md", "README.md",
        "build.sh", "compose.yaml", "images.env", "package.py", "preflight-benchmark.sh",
        "run-benchmark.sh", "run.sh", "summarize_fuzz_log.py", "source-lock.json",
        "toolchain-lock.json", "source", "build-logs", "results",
    }
    files: list[Path] = []
    for name in sorted(explicit):
        path = ROOT / name
        if not path.exists():
            raise RuntimeError(f"declared package input missing: {name}")
        files.extend([path] if path.is_file() else [p for p in path.rglob("*") if p.is_file()])
    return sorted({p for p in files if "__pycache__" not in p.parts and ".gocache" not in p.parts and p.suffix != ".pyc"})


def main() -> int:
    candidate = sys.argv[1:] == ["--candidate"]
    if len(sys.argv) > 1 and not candidate:
        raise RuntimeError("usage: package.py [--candidate]")
    lock = load_json(ROOT / "source-lock.json")
    verify_hash(ROOT / lock["source_archive"], lock["source_archive_sha256"])
    verify_hash(ROOT / lock["toolchain_archive"], lock["toolchain_archive_sha256"])
    preflight = check_run(PREFLIGHT, formal=False)
    formal = check_run(CAMPAIGN, formal=True)
    verify_times(PREFLIGHT, minimum_seconds=55)
    verify_times(CAMPAIGN, minimum_seconds=1800)
    if preflight.get("final_execs", 0) <= 0 or formal.get("final_execs", 0) <= 0:
        raise RuntimeError("native fuzz engine recorded no executions")

    acceptance = (ROOT / "ACCEPTANCE.md").read_text(encoding="utf-8").lower()
    cleanup = load_json(ROOT / "build-logs/image-cleanup.json")
    if cleanup.get("image_tag") != IMAGE:
        raise RuntimeError("cleanup record refers to a different image")
    if candidate:
        if cleanup.get("status") != "pending" or cleanup.get("image_absent_after"):
            raise RuntimeError("candidate package requires pending cleanup evidence")
        if "packaging and image cleanup pending" not in acceptance:
            raise RuntimeError("candidate package requires pending finalization status")
        output = CANDIDATE_ZIP
    else:
        if cleanup.get("status") != "removed" or not cleanup.get("image_absent_after"):
            raise RuntimeError("final package requires verified image removal")
        if "status: complete" not in acceptance:
            raise RuntimeError("final package requires a complete acceptance record")
        output = FINAL_ZIP

    files = collect_files()
    manifest = "\n".join(
        f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(ROOT).as_posix()}"
        for path in files
    ) + "\n"
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in files:
            archive.write(path, Path(ROOT_NAME) / path.relative_to(ROOT))
        archive.writestr(f"{ROOT_NAME}/MANIFEST.SHA256", manifest)
    with zipfile.ZipFile(output) as archive:
        bad = archive.testzip()
        if bad:
            raise RuntimeError(f"ZIP CRC check failed: {bad}")
        if any("基准化经验库" in name for name in archive.namelist()):
            raise RuntimeError("central aggregated experience library must stay outside this ZIP")
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix(output.suffix + ".sha256").write_text(
        f"{digest}  {output.name}\n", encoding="ascii")
    print(f"PASS: {output} ({output.stat().st_size} bytes), SHA-256 {digest}")
    print(f"preflight: {preflight['final_execs']} executions; formal: {formal['final_execs']} executions")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, KeyError, zipfile.BadZipFile) as exc:
        print(f"package validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
