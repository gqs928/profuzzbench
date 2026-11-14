#!/usr/bin/env python3
"""Validate ngtcp2 baseline evidence and create its standalone ZIP."""
from __future__ import annotations

import hashlib
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEST = ROOT.parent / "deliverables/12-protocol-baselines-2026-11-03-framework"
PREFLIGHT = ROOT / "results/ngtcp2-preflight-60s-20261113"
CAMPAIGN = ROOT / "results/ngtcp2-fuzz-30m-20261113"
IMAGE = "ngtcp2-aflnet-bench:v1.26.0"
ZIP = DEST / "71-ngtcp2-QUIC-1.26.0.zip"
CANDIDATE_ZIP = Path("/tmp/71-ngtcp2-QUIC-1.26.0-precleanup.zip")
CORE_FILES = [
    ".dockerignore", "ACCEPTANCE.md", "Dockerfile", "PACKAGE-MANIFEST.md", "README.md",
    "build.sh", "build-info.sh", "compose.yaml", "deadline_wrapper.py", "images.env",
    "package.py", "patches/aflnet-quic.patch", "patches/expand-aflnet-map.py",
    "patches/fix-aflnet-toolchain.py", "preflight-benchmark.sh", "protocol_smoke.py",
    "replay_queue.py", "run-benchmark.sh", "run.sh", "source-lock.json",
    "toolchain-lock.json", "validate_seeds.py", "verify_listener_closed.py",
    "seeds/quic-v1-client-initial.bin", "source", "build-logs", "results/seed-validation.json",
    "results/ngtcp2-preflight-60s-20261113", "results/ngtcp2-fuzz-30m-20261113",
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
    report = load_json(path)
    kinds = {"initial", "handshake", "retry", "version-negotiation"}
    rows = report.get("checks", [])
    if report.get("passes") != 3 or not report.get("all_responses_valid") or len(rows) != 3:
        raise RuntimeError(f"QUIC smoke did not complete three valid passes: {path}")
    if any(row.get("request_packet_type") != "initial" or
           row.get("response_packet_type") not in kinds or
           not row.get("server_alive_after_request") or
           not row.get("server_exit_after_controlled_sigterm") or
           not row.get("listener_released") for row in rows):
        raise RuntimeError(f"QUIC smoke lifecycle/response check failed: {path}")


def check_run(run: Path, seconds: int, expected_stability: float | None = None) -> None:
    deadline = load_json(run / "fuzzer-deadline.json")
    stats = parse_stats(run / "fuzzer_stats")
    if not deadline.get("deadline_reached") or deadline.get("requested_duration_seconds") != seconds:
        raise RuntimeError(f"campaign deadline not reached: {run}")
    if deadline.get("child_return_code") != 0 or abs(float(deadline.get("elapsed_seconds", -1)) - seconds) > 1:
        raise RuntimeError(f"deadline supervisor/child status mismatch: {run}")
    stats_span = int(stats.get("last_update", "0")) - int(stats.get("start_time", "0"))
    if (seconds == 1800 and not seconds <= stats_span <= seconds + 5) or \
       (seconds == 60 and not 55 <= stats_span <= 65):
        raise RuntimeError(f"unexpected fuzzer_stats duration {stats_span}: {run}")
    if int(stats.get("execs_done", "0")) <= 0 or int(stats.get("paths_total", "0")) <= 0:
        raise RuntimeError(f"no fuzz progress was recorded: {run}")
    if float(stats.get("bitmap_cvg", "0%").rstrip("%")) <= 0:
        raise RuntimeError(f"no feedback map activity was recorded: {run}")
    if int(stats.get("unique_crashes", "-1")) != 0 or int(stats.get("unique_hangs", "-1")) != 0:
        raise RuntimeError(f"unique crash/hang count is nonzero: {run}")
    stability = float(stats.get("stability", "0%").rstrip("%"))
    if expected_stability is not None and stability != expected_stability:
        raise RuntimeError(f"unexpected stability {stability}: {run}")
    check_smoke(run / "preflight-smoke.json")
    check_smoke(run / "postrun-smoke.json")
    if not load_json(run / "listener-closed.json").get("listener_closed"):
        raise RuntimeError(f"listener remained open after campaign: {run}")
    replay = load_json(run / "replay-summary.json")
    samples = int(replay.get("samples_total", -1))
    records = replay.get("records", [])
    if samples <= 0 or len(records) != samples or replay.get("listeners_released") != samples:
        raise RuntimeError(f"queue replay is incomplete: {run}")
    if any(not row.get("target_started") or not row.get("target_alive_after_input") or
           not row.get("clean_sigterm_exit") or not row.get("listener_released")
           for row in records):
        raise RuntimeError(f"queue replay found unhealthy target lifecycle: {run}")
    for kind, counter in (("hangs", "unique_hangs"), ("crashes", "unique_crashes")):
        summary = load_json(run / f"{kind}-replay-summary.json")
        count = int(stats.get(counter, "0"))
        if summary.get("samples_total") != count:
            raise RuntimeError(f"{kind} replay count does not match fuzzer_stats: {run}")
    if not load_json(run / "replay-listener-closed.json").get("listener_closed"):
        raise RuntimeError(f"listener remained open after queue replay: {run}")


def verify_hash(path: Path, expected: str) -> None:
    require(path)
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != expected:
        raise RuntimeError(f"locked SHA-256 mismatch: {path.relative_to(ROOT)} ({actual})")


def main() -> int:
    candidate_mode = sys.argv[1:] == ["--candidate"]
    if len(sys.argv) > 1 and not candidate_mode:
        raise RuntimeError("usage: package.py [--candidate]")
    lock = load_json(ROOT / "source-lock.json")
    toolchain = load_json(ROOT / "toolchain-lock.json")
    verify_hash(ROOT / "source" / lock["source_archive"], lock["source_sha256"])
    for entry in lock["submodules"].values():
        verify_hash(ROOT / "source" / entry["archive"], entry["sha256"])
    for dependency in (lock["http3_dependency"], lock["tls_dependency"]):
        verify_hash(ROOT / "source" / dependency["archive"], dependency["sha256"])
        for entry in dependency.get("submodules", {}).values():
            verify_hash(ROOT / "source" / entry["archive"], entry["sha256"])
    verify_hash(ROOT / "source" / lock["aflnet_archive"], lock["aflnet_sha256"])
    verify_hash(ROOT / lock["aflnet_patch"], lock["aflnet_patch_sha256"])
    verify_hash(ROOT / lock["aflnet_map_size_script"], lock["aflnet_map_size_script_sha256"])
    adapter = lock.get("aflnet_toolchain_compatibility_patch", {})
    verify_hash(ROOT / adapter["path"], adapter["sha256"])
    verify_hash(ROOT / lock["seed"], lock["seed_sha256"])
    if toolchain.get("aflnet_map_size") != 262144:
        raise RuntimeError("toolchain profile map size differs from 262144")
    seed_report = load_json(ROOT / "results/seed-validation.json")
    if not seed_report.get("valid") or not seed_report.get("datagram_atomic"):
        raise RuntimeError("QUIC seed validation did not pass")

    for path in (
        ROOT / "build-logs/docker-build.log", ROOT / "build-logs/image-id.txt",
        ROOT / "build-logs/build-info.txt", ROOT / "build-logs/image-cleanup.json",
        ROOT / "ACCEPTANCE.md", ROOT / "README.md", ROOT / "PACKAGE-MANIFEST.md",
        PREFLIGHT / "run-parameters.txt", PREFLIGHT / "fuzzer_stats", PREFLIGHT / "plot_data",
        CAMPAIGN / "run-parameters.txt", CAMPAIGN / "fuzzer_stats", CAMPAIGN / "plot_data",
        CAMPAIGN / "fuzzer-deadline.json", CAMPAIGN / "queue",
    ):
        if path.is_dir():
            if not any(item.is_file() for item in path.iterdir()):
                raise RuntimeError(f"required evidence directory is empty: {path}")
        else:
            require(path)
    check_run(PREFLIGHT, 60)
    check_run(CAMPAIGN, 1800, 97.78)

    acceptance = (ROOT / "ACCEPTANCE.md").read_text(encoding="utf-8").lower()
    cleanup = load_json(ROOT / "build-logs/image-cleanup.json")
    if cleanup.get("image_tag") != IMAGE:
        raise RuntimeError("cleanup record refers to a different image")
    if candidate_mode:
        if "status: benchmark passed; packaging and image cleanup pending" not in acceptance:
            raise RuntimeError("candidate ZIP requires passed benchmark/finalization pending status")
        if cleanup.get("status") != "pending" or cleanup.get("image_absent_after"):
            raise RuntimeError("candidate ZIP cleanup evidence must remain pending")
    else:
        if "status: complete" not in acceptance or not cleanup.get("image_absent_after"):
            raise RuntimeError("final package requires complete acceptance and verified cleanup")

    DEST.mkdir(parents=True, exist_ok=True)
    output_zip = CANDIDATE_ZIP if candidate_mode else ZIP
    if output_zip.exists():
        output_zip.unlink()
    files: set[Path] = set()
    for name in CORE_FILES:
        path = ROOT / name
        if not path.exists():
            raise RuntimeError(f"declared package input missing: {name}")
        if path.is_file():
            files.add(path)
        else:
            files.update(item for item in path.rglob("*") if item.is_file())
    files = {path for path in files if "__pycache__" not in path.parts and path.suffix != ".pyc"}
    manifest = [f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(ROOT).as_posix()}"
                for p in sorted(files)]
    root_name = "ngtcp2-QUIC-1.26.0"
    with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in sorted(files):
            archive.write(path, Path(root_name) / path.relative_to(ROOT))
        archive.writestr(f"{root_name}/MANIFEST.SHA256", "\n".join(manifest) + "\n")
    with zipfile.ZipFile(output_zip) as archive:
        bad = archive.testzip()
        if bad:
            raise RuntimeError(f"ZIP CRC check failed: {bad}")
        if any("基准化经验库" in name for name in archive.namelist()):
            raise RuntimeError("central experience library must not be in the target ZIP")
    digest = hashlib.sha256(output_zip.read_bytes()).hexdigest()
    output_zip.with_suffix(output_zip.suffix + ".sha256").write_text(
        f"{digest}  {output_zip.name}\n", encoding="ascii")
    print(f"PASS: {output_zip} ({output_zip.stat().st_size} bytes), SHA-256 {digest}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, KeyError, zipfile.BadZipFile) as exc:
        print(f"package validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
