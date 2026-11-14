#!/usr/bin/env python3
"""Validate Cloudflare quiche evidence and build a standalone protocol ZIP."""
from __future__ import annotations

import hashlib
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PREFLIGHT = ROOT / "results/quiche-preflight-60s-20261112"
CAMPAIGN = ROOT / "results/quiche-fuzz-30m-20261112"
DEST = ROOT.parent / "deliverables/12-protocol-baselines-2026-11-03-framework"
ZIP = DEST / "67-Cloudflare-quiche-QUIC-0.30.0.zip"
IMAGE = "cloudflare-quiche-aflnet-bench:0.30.0"
INCLUDE = [
    ".dockerignore", "ACCEPTANCE.md", "Dockerfile", "Dockerfile.aflnet-compat", "PACKAGE-MANIFEST.md", "README.md",
    "build.sh", "build-info.sh", "compose.yaml", "deadline_wrapper.py", "generate-seeds.sh",
    "images.env", "package.py", "patches/aflnet-quic.patch", "patches/expand-aflnet-map.py", "patches/quiche-add-seedgen.patch",
    "preflight-benchmark.sh", "protocol_smoke.py", "replay_queue.py", "run-benchmark.sh",
    "run.sh", "source/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz",
    "source/quiche-0.30.0.tar.gz", "source-lock.json", "target.sh", "toolchain-lock.json",
    "validate_seeds.py", "verify_listener_closed.py", "seeds",
    "build-logs", "results/seed-generation-console.log", "results/quiche-seeds-validation.json",
    "results/quiche-seed.sha256", "results/quiche-preflight-60s-20261112-console.log",
    "results/quiche-fuzz-30m-20261112-console.log", "results/quiche-preflight-60s-20261112",
    "results/quiche-fuzz-30m-20261112",
]


def require(path: Path) -> None:
    if not path.is_file() or path.stat().st_size == 0:
        raise RuntimeError(f"required evidence missing or empty: {path.relative_to(ROOT)}")


def load_json(path: Path) -> dict:
    require(path)
    return json.loads(path.read_text(encoding="utf-8"))


def parse_stats(path: Path) -> dict[str, str]:
    require(path)
    values: dict[str, str] = {}
    for line in path.read_text(errors="replace").splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            values[key.strip()] = value.strip()
    return values


def check_smoke(path: Path) -> None:
    smoke = load_json(path)
    if smoke.get("passes") != 3 or not smoke.get("all_responses_valid"):
        raise RuntimeError(f"QUIC Initial smoke failed: {path}: {smoke}")
    checks = smoke.get("checks", [])
    if len(checks) != 3 or any(
        row.get("request_packet_type") != "initial" or
        row.get("response_packet_type") not in ("initial", "handshake") or
        not row.get("server_alive_after_request") or
        not row.get("server_exit_after_controlled_sigterm") or
        not row.get("listener_released")
        for row in checks
    ):
        raise RuntimeError(f"QUIC smoke did not verify three valid Initial/response/cleanup cycles: {path}")


def check_replay(summary_path: Path, sample_dir: Path, expected_count: int, *, expect_live: bool) -> None:
    summary = load_json(summary_path)
    files = sum(1 for p in sample_dir.iterdir() if p.is_file() and not p.name.startswith("."))
    if summary.get("samples_total") != files or files != expected_count:
        raise RuntimeError(f"replay coverage mismatch in {summary_path}: {summary.get('samples_total')} / {files} / {expected_count}")
    records = summary.get("records", [])
    if len(records) != files or any(not row.get("target_started") or not row.get("listener_released") for row in records):
        raise RuntimeError(f"not every sample started a server and released its UDP listener: {summary_path}")
    if expect_live and any(
        not row.get("target_alive_after_input") or not row.get("clean_sigterm_exit")
        for row in records
    ):
        raise RuntimeError(f"ordinary queue replay found unexpected target exit: {summary_path}")
    if summary.get("listeners_released") != files:
        raise RuntimeError(f"not every replay released its UDP port: {summary_path}")


def main() -> int:
    lock = load_json(ROOT / "source-lock.json")
    toolchain = load_json(ROOT / "toolchain-lock.json")
    for name, expected in (
        (lock["source_archive"], lock["source_sha256"]),
        (lock["aflnet_archive"], lock["aflnet_sha256"]),
        ("patches/aflnet-quic.patch", lock["aflnet_patch_sha256"]),
        ("patches/expand-aflnet-map.py", lock["aflnet_map_size_script_sha256"]),
        ("patches/quiche-add-seedgen.patch", lock["seedgen_patch_sha256"]),
    ):
        path = ROOT / name if name.startswith("patches/") else ROOT / "source" / name
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise RuntimeError(f"locked SHA-256 mismatch: {path.relative_to(ROOT)}")
    if toolchain.get("rust_toolchain") != "1.100.0" or toolchain.get("cargo_afl") != "0.18.2":
        raise RuntimeError("toolchain lock does not match the accepted quiche profile")

    seed_validation = load_json(ROOT / "results/quiche-seeds-validation.json")
    if not seed_validation.get("valid") or not seed_validation.get("datagram_atomic"):
        raise RuntimeError("generated QUIC seed validation failed")
    seed_hash = (ROOT / "results/quiche-seed.sha256").read_text(encoding="ascii").split()[0]
    seed = ROOT / "seeds/quic-v1-client-initial.bin"
    if hashlib.sha256(seed.read_bytes()).hexdigest() != seed_hash:
        raise RuntimeError("generated QUIC seed SHA-256 mismatch")

    for path in (
        ROOT / "build-logs/docker-build.log", ROOT / "build-logs/image-id.txt",
        ROOT / "build-logs/build-info.txt", ROOT / "build-logs/quiche-Cargo.lock",
        ROOT / "results/seed-generation-console.log",
        ROOT / "results/quiche-preflight-60s-20261112-console.log",
        ROOT / "results/quiche-fuzz-30m-20261112-console.log",
        PREFLIGHT / "fuzzer_stats", PREFLIGHT / "fuzzer-deadline.json",
        PREFLIGHT / "seeds-validation.json", PREFLIGHT / "preflight-smoke.json",
        PREFLIGHT / "postrun-smoke.json", PREFLIGHT / "listener-closed.json",
        PREFLIGHT / "replay-summary.json", PREFLIGHT / "hangs-replay-summary.json",
        PREFLIGHT / "crashes-replay-summary.json",
        CAMPAIGN / "fuzzer_stats", CAMPAIGN / "plot_data", CAMPAIGN / "run-parameters.txt",
        CAMPAIGN / "fuzzer-deadline.json", CAMPAIGN / "seeds-validation.json",
        CAMPAIGN / "preflight-smoke.json", CAMPAIGN / "postrun-smoke.json",
        CAMPAIGN / "listener-closed.json", CAMPAIGN / "replay-summary.json",
        CAMPAIGN / "hangs-replay-summary.json", CAMPAIGN / "crashes-replay-summary.json",
        CAMPAIGN / "replay-listener-closed.json", ROOT / "ACCEPTANCE.md",
        ROOT / "README.md", ROOT / "PACKAGE-MANIFEST.md",
    ):
        require(path)

    for run, requested in ((PREFLIGHT, 60), (CAMPAIGN, 1800)):
        deadline = load_json(run / "fuzzer-deadline.json")
        if not deadline.get("deadline_reached") or deadline.get("requested_duration_seconds") != requested:
            raise RuntimeError(f"deadline supervisor did not complete the requested duration: {deadline}")
        stats = parse_stats(run / "fuzzer_stats")
        span = int(stats.get("last_update", "0")) - int(stats.get("start_time", "0"))
        if requested == 1800:
            elapsed = float(deadline.get("elapsed_seconds", 0))
            # AFL's whole-second stats timestamps include startup/shutdown bookkeeping;
            # the supervisor's monotonic deadline is the authoritative wall-clock bound.
            if not 1799 <= elapsed <= 1801:
                raise RuntimeError(f"formal supervisor elapsed time is outside the 30-minute bound: {elapsed}")
            if not 1798 <= span <= 1805:
                raise RuntimeError(f"formal fuzzer stats span is outside the expected coarse-clock range: {span}")
        if requested == 60 and span < 55:
            raise RuntimeError(f"preflight fuzzer stats span is too short: {span}")
        if requested == 60 and float(stats.get("bitmap_cvg", "0%").rstrip("%")) <= 0:
            raise RuntimeError("preflight shows no AFL feedback from the instrumented target")
        check_smoke(run / "preflight-smoke.json")
        check_smoke(run / "postrun-smoke.json")
        if not load_json(run / "listener-closed.json").get("listener_closed"):
            raise RuntimeError(f"listener remained active after campaign: {run}")
        qdir = run / "queue"
        qstats = load_json(run / "replay-summary.json")
        check_replay(run / "replay-summary.json", qdir, int(qstats.get("samples_total", -1)), expect_live=True)
        for kind, summary_name, stats_key, expected_live in (
            ("replayable-hangs", "hangs-replay-summary.json", "unique_hangs", False),
            ("replayable-crashes", "crashes-replay-summary.json", "unique_crashes", False),
        ):
            sdir = run / kind
            sdir.mkdir(parents=True, exist_ok=True)
            fuzz_stats = parse_stats(run / "fuzzer_stats")
            expected = int(fuzz_stats.get(stats_key, "0"))
            check_replay(run / summary_name, sdir, expected, expect_live=expected_live)
        if not load_json(run / "replay-listener-closed.json").get("listener_closed"):
            raise RuntimeError(f"listener remained active after sample replay: {run}")

    if "status: complete" not in (ROOT / "ACCEPTANCE.md").read_text(encoding="utf-8").lower():
        raise RuntimeError("ACCEPTANCE.md must say status: complete before packaging")
    cleanup = load_json(ROOT / "build-logs/image-cleanup.json")
    if not cleanup.get("image_absent_after") or cleanup.get("image_tag") != IMAGE:
        raise RuntimeError("the exact dedicated quiche image was not verified absent")

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
    manifests = []
    for path in sorted(files):
        rel = path.relative_to(ROOT).as_posix()
        manifests.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {rel}")
    with zipfile.ZipFile(ZIP, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in sorted(files):
            archive.write(path, Path("Cloudflare-quiche-QUIC-0.30.0") / path.relative_to(ROOT))
        archive.writestr("Cloudflare-quiche-QUIC-0.30.0/MANIFEST.SHA256", "\n".join(manifests) + "\n")
    with zipfile.ZipFile(ZIP) as archive:
        bad = archive.testzip()
        if bad:
            raise RuntimeError(f"ZIP CRC check failed: {bad}")
        names = set(archive.namelist())
        if any("基准化经验库" in name for name in names):
            raise RuntimeError("the central experience library must not be included in the protocol ZIP")
    digest = hashlib.sha256(ZIP.read_bytes()).hexdigest()
    ZIP.with_suffix(ZIP.suffix + ".sha256").write_text(f"{digest}  {ZIP.name}\n", encoding="ascii")
    print(f"PASS: {ZIP} ({ZIP.stat().st_size} bytes), SHA-256 {digest}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, zipfile.BadZipFile, KeyError) as exc:
        print(f"package validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
