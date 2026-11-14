#!/usr/bin/env python3
"""Validate and package the standalone Picoquic QUIC baseline evidence."""
from __future__ import annotations

import hashlib
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEST = ROOT.parent / "deliverables/12-protocol-baselines-2026-11-03-framework"
PREFLIGHT = ROOT / "results/picoquic-preflight-60s-20261113-attempt-2"
CAMPAIGN = ROOT / "results/picoquic-fuzz-30m-20261113"
IMAGE = "picoquic-aflnet-bench:v2026.11.12.36f49b7"
FINAL_ZIP = DEST / "73-Picoquic-QUIC-v2026.11.12.36f49b7.zip"
CANDIDATE_ZIP = Path("/tmp/73-Picoquic-QUIC-v2026.11.12.36f49b7-precleanup.zip")
ROOT_NAME = "picoquic-QUIC-v2026.11.12.36f49b7"


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


def parse_stats(path: Path) -> dict[str, str]:
    if not path.is_file() or not path.stat().st_size:
        raise RuntimeError(f"AFLNet stats missing: {path.relative_to(ROOT)}")
    values = {}
    for line in path.read_text(errors="replace").splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            values[key.strip()] = value.strip()
    return values


def check_smoke(path: Path) -> None:
    report = load_json(path)
    rows = report.get("checks", [])
    if report.get("passes") != 3 or not report.get("all_responses_valid") or len(rows) != 3:
        raise RuntimeError(f"three-pass QUIC smoke did not pass: {path.relative_to(ROOT)}")
    if any(row.get("request_packet_type") != "initial" or
           row.get("response_packet_type") != "initial" or
           row.get("response_bytes") != 51 or
           not row.get("server_alive_after_request") or
           not row.get("server_exit_after_controlled_sigterm") or
           not row.get("listener_released") for row in rows):
        raise RuntimeError(f"QUIC Initial response or lifecycle check failed: {path.relative_to(ROOT)}")


def check_run(run: Path, seconds: int, *, formal: bool) -> dict[str, str]:
    deadline = load_json(run / "fuzzer-deadline.json")
    stats = parse_stats(run / "fuzzer_stats")
    if (not deadline.get("deadline_reached") or
            deadline.get("requested_duration_seconds") != seconds or
            deadline.get("child_return_code") != 0 or
            abs(float(deadline.get("elapsed_seconds", -1)) - seconds) > 1):
        raise RuntimeError(f"deadline supervisor result failed: {run.relative_to(ROOT)}")
    span = int(stats.get("last_update", "0")) - int(stats.get("start_time", "0"))
    if (seconds == 1800 and not seconds <= span <= seconds + 5) or \
       (seconds == 60 and not 55 <= span <= 65):
        raise RuntimeError(f"unexpected AFLNet stats span {span}: {run.relative_to(ROOT)}")
    if int(stats.get("execs_done", "0")) <= 0 or int(stats.get("paths_total", "0")) <= 0:
        raise RuntimeError(f"AFLNet recorded no progress: {run.relative_to(ROOT)}")
    if float(stats.get("bitmap_cvg", "0%").rstrip("%")) <= 0:
        raise RuntimeError(f"AFLNet feedback bitmap stayed empty: {run.relative_to(ROOT)}")
    if int(stats.get("unique_crashes", "-1")) != 0 or int(stats.get("unique_hangs", "-1")) != 0:
        raise RuntimeError(f"unique crash/hang count is nonzero: {run.relative_to(ROOT)}")
    if formal and float(stats.get("stability", "0%").rstrip("%")) < 90:
        raise RuntimeError("formal AFLNet stability is below the 90% review gate")
    check_smoke(run / "preflight-smoke.json")
    check_smoke(run / "postrun-smoke.json")
    if not load_json(run / "listener-closed.json").get("listener_closed"):
        raise RuntimeError(f"UDP listener remained open: {run.relative_to(ROOT)}")
    replay = load_json(run / "replay-summary.json")
    samples = int(replay.get("samples_total", -1))
    records = replay.get("records", [])
    if samples <= 0 or samples != len(records) or replay.get("listeners_released") != samples:
        raise RuntimeError(f"queue replay is incomplete: {run.relative_to(ROOT)}")
    if any(not row.get("target_started") or not row.get("target_alive_after_input") or
           not row.get("clean_sigterm_exit") or not row.get("listener_released")
           for row in records):
        raise RuntimeError(f"queue replay found unhealthy target lifecycle: {run.relative_to(ROOT)}")
    for kind, field in (("hangs", "unique_hangs"), ("crashes", "unique_crashes")):
        summary = load_json(run / f"{kind}-replay-summary.json")
        if int(summary.get("samples_total", -1)) != int(stats[field]):
            raise RuntimeError(f"{kind} replay count disagrees with AFLNet stats")
    if not load_json(run / "replay-listener-closed.json").get("listener_closed"):
        raise RuntimeError(f"listener remained open after replay: {run.relative_to(ROOT)}")
    return stats


def collect_files() -> list[Path]:
    explicit = {
        ".dockerignore", "ACCEPTANCE.md", "Dockerfile", "PACKAGE-MANIFEST.md", "README.md",
        "build.sh", "build-info.sh", "compose.yaml", "deadline_wrapper.py", "images.env",
        "package.py", "patches", "preflight-benchmark.sh", "protocol_smoke.py", "replay_queue.py",
        "run-benchmark.sh", "run.sh", "source-lock.json", "toolchain-lock.json",
        "validate_seeds.py", "verify_listener_closed.py", "seeds", "source", "build-logs", "results",
    }
    files: list[Path] = []
    for name in sorted(explicit):
        path = ROOT / name
        if not path.exists():
            raise RuntimeError(f"declared package input missing: {name}")
        files.extend([path] if path.is_file() else [item for item in path.rglob("*") if item.is_file()])
    return sorted({p for p in files if "__pycache__" not in p.parts and p.suffix != ".pyc"})


def main() -> int:
    candidate = sys.argv[1:] == ["--candidate"]
    if len(sys.argv) > 1 and not candidate:
        raise RuntimeError("usage: package.py [--candidate]")
    lock = load_json(ROOT / "source-lock.json")
    verify_hash(ROOT / lock["source_archive"], lock["source_archive_sha256"])
    verify_hash(ROOT / lock["picotls_archive"], lock["picotls_archive_sha256"])
    verify_hash(ROOT / lock["picotest_archive"], lock["picotest_archive_sha256"])
    verify_hash(ROOT / lock["aflnet_archive"], lock["aflnet_archive_sha256"])
    for key in ("aflnet_patch", "aflnet_map_size_script", "aflnet_build_adapter", "seed"):
        hash_key = {
            "aflnet_patch": "aflnet_patch_sha256",
            "aflnet_map_size_script": "aflnet_map_size_script_sha256",
            "aflnet_build_adapter": "aflnet_build_adapter_sha256",
            "seed": "seed_sha256",
        }[key]
        verify_hash(ROOT / lock[key], lock[hash_key])
    if lock.get("coverage_map_size") != 262144:
        raise RuntimeError("source lock does not specify AFLNet map size 262144")
    seed_report = load_json(PREFLIGHT / "seeds-validation.json")
    if not seed_report.get("valid") or not seed_report.get("datagram_atomic"):
        raise RuntimeError("QUIC Initial seed validation failed")
    preflight_stats = check_run(PREFLIGHT, 60, formal=False)
    formal_stats = check_run(CAMPAIGN, 1800, formal=True)
    if float(preflight_stats.get("stability", "0%").rstrip("%")) < 90:
        raise RuntimeError("short preflight stability is below the gate")

    acceptance = (ROOT / "ACCEPTANCE.md").read_text(encoding="utf-8").lower()
    cleanup = load_json(ROOT / "build-logs/image-cleanup.json")
    if cleanup.get("image_tag") != IMAGE:
        raise RuntimeError("cleanup record refers to a different image")
    if candidate:
        if cleanup.get("status") != "pending" or cleanup.get("image_absent_after"):
            raise RuntimeError("candidate ZIP requires pending image-cleanup evidence")
        if "packaging and image cleanup pending" not in acceptance:
            raise RuntimeError("candidate ZIP requires pending finalization status")
        output = CANDIDATE_ZIP
    else:
        if cleanup.get("status") != "removed" or not cleanup.get("image_absent_after"):
            raise RuntimeError("final ZIP requires verified image removal")
        if "status: complete" not in acceptance:
            raise RuntimeError("final ZIP requires complete acceptance status")
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
            raise RuntimeError("the aggregated experience library must remain outside this protocol ZIP")
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix(output.suffix + ".sha256").write_text(
        f"{digest}  {output.name}\n", encoding="ascii")
    print(f"PASS: {output} ({output.stat().st_size} bytes), SHA-256 {digest}")
    print(f"formal: {formal_stats['execs_done']} execs, {formal_stats['paths_total']} paths, "
          f"{formal_stats['stability']} stability, {formal_stats['bitmap_cvg']} AFL bitmap, "
          f"variable_paths={formal_stats['variable_paths']}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, KeyError, zipfile.BadZipFile) as exc:
        print(f"package validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
