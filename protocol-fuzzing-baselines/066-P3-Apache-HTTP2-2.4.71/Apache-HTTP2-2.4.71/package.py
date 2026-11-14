#!/usr/bin/env python3
"""Validate Apache HTTP/2 evidence and build its standalone protocol ZIP."""
from __future__ import annotations

import hashlib
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CAMPAIGN = ROOT / "results" / "apache-http2-fuzz-30m-20261112"
PREFLIGHT = ROOT / "results" / "apache-http2-preflight-60s-20261112"
DEST = ROOT.parent / "deliverables" / "12-protocol-baselines-2026-11-03-framework"
ZIP = DEST / "66-Apache-HTTP2-2.4.71.zip"
INCLUDE = [
    ".dockerignore", "ACCEPTANCE.md", "Dockerfile", "PACKAGE-MANIFEST.md", "README.md",
    "build.sh", "build-logs", "compose.yaml", "deadline_wrapper.py", "httpd.conf",
    "images.env", "make_seeds.py", "package.py", "patches", "preflight-benchmark.sh",
    "preflight.sh", "prepare-target.sh", "protocol_smoke.py", "replay_queue.py",
    "run-benchmark.sh", "run.sh", "seeds", "seeds-manifest.json", "source",
    "source-lock.json", "stop-target.sh", "target.sh", "target-version.txt",
    "results/preflight-attempt-1-script-target-rejected.log",
    "results/preflight-attempt-1-target-script-rejected",
    "results/preflight-attempt-2-uninstrumented-launcher-rejected",
    "results/preflight-attempt-2-uninstrumented-launcher-rejected.log",
    "results/preflight-attempt-3-instrumented-launcher-zero-stability",
    "results/preflight-attempt-3-instrumented-launcher-zero-stability.log",
    "results/preflight-attempt-4-uninstrumented-supervisor-zero-stability",
    "results/preflight-attempt-4-uninstrumented-supervisor-zero-stability.log",
    "results/preflight-attempt-5-direct-httpd-seed-crash",
    "results/preflight-attempt-6-direct-httpd-signal11",
    "results/preflight-attempt-7-forkserver-apache-signal11",
    "results/preflight-attempt-8-forkserver-zero-stability",
    "validate_seeds.py", "verify_listener_closed.py", "www",
    "results/campaign-console.log", "results/preflight-console.log",
    "results/apache-http2-preflight-60s-20261112",
    "results/apache-http2-fuzz-30m-20261112",
]


def require(path: Path) -> None:
    if not path.is_file() or path.stat().st_size == 0:
        raise RuntimeError(f"required evidence missing or empty: {path.relative_to(ROOT)}")


def load_json(path: Path) -> dict:
    require(path)
    return json.loads(path.read_text(encoding="utf-8"))


def parse_stats(path: Path) -> dict[str, str]:
    require(path)
    stats = {}
    for line in path.read_text(errors="replace").splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            stats[key.strip()] = value.strip()
    return stats


def check_smoke(path: Path) -> None:
    smoke = load_json(path)
    if smoke.get("passes") != 3 or not smoke.get("all_responses_valid"):
        raise RuntimeError(f"HTTP/2 smoke failed: {path.name}: {smoke}")
    if len(smoke.get("checks", [])) != 3 or any(
        item.get("status") != "200" or not item.get("stream_ended") or not item.get("marker_seen")
        for item in smoke["checks"]
    ):
        raise RuntimeError(f"HTTP/2 smoke did not verify all three responses: {path.name}")


def main() -> int:
    pre_clean = "--pre-clean" in sys.argv[1:]
    lock = load_json(ROOT / "source-lock.json")
    for name, expected in ((lock["source_archive"], lock["source_sha256"]),):
        actual = hashlib.sha256((ROOT / "source" / name).read_bytes()).hexdigest()
        if actual != expected:
            raise RuntimeError(f"source SHA-256 mismatch: {name}")
    patch_hash = hashlib.sha256((ROOT / "patches/aflnet-http2.patch").read_bytes()).hexdigest()
    if patch_hash != lock["aflnet_patch_sha256"]:
        raise RuntimeError("AFLNet HTTP/2 patch SHA-256 mismatch")
    for path in (ROOT / "ACCEPTANCE.md", ROOT / "PACKAGE-MANIFEST.md", ROOT / "README.md",
                 ROOT / "build-logs/build.log", ROOT / "build-logs/image-id.txt",
                 ROOT / "build-logs/source-pgp-check.txt", ROOT / "build-logs/source-sha256-check.txt",
                 ROOT / "results/preflight-console.log",
                 ROOT / "source/httpd-2.4.71.tar.bz2", ROOT / "source/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz",
                 PREFLIGHT / "fuzzer_stats", PREFLIGHT / "fuzzer-deadline.json",
                 PREFLIGHT / "preflight-smoke.json", PREFLIGHT / "postrun-smoke.json",
                 PREFLIGHT / "listener-closed.json", CAMPAIGN / "fuzzer_stats",
                 CAMPAIGN / "plot_data", CAMPAIGN / "run-parameters.txt",
                 CAMPAIGN / "fuzzer-deadline.json", CAMPAIGN / "preflight-smoke.json",
                 CAMPAIGN / "postrun-smoke.json", CAMPAIGN / "listener-closed.json",
                 CAMPAIGN / "replay-summary.json", CAMPAIGN / "hangs-replay-summary.json",
                 CAMPAIGN / "replay-listener-closed.json"):
        require(path)
    deadline = load_json(CAMPAIGN / "fuzzer-deadline.json")
    if not deadline.get("deadline_reached") or deadline.get("stop_method") not in ("SIGINT", "SIGTERM"):
        raise RuntimeError(f"formal campaign did not reach its bounded deadline: {deadline}")
    stats = parse_stats(CAMPAIGN / "fuzzer_stats")
    runtime = int(stats.get("last_update", "0")) - int(stats.get("start_time", "0"))
    if runtime not in (1800, 1801):
        raise RuntimeError(f"AFLNet stats span is outside the 1,800-second window: {runtime}")
    if int(stats.get("unique_crashes", "-1")):
        raise RuntimeError("formal campaign reports crashes")
    formal_hangs = int(stats.get("unique_hangs", "-1"))
    if formal_hangs < 0:
        raise RuntimeError("formal campaign hang count is unavailable")
    pre_stats = parse_stats(PREFLIGHT / "fuzzer_stats")
    if int(pre_stats.get("unique_crashes", "-1")) or int(pre_stats.get("unique_hangs", "-1")):
        raise RuntimeError("preflight reports crashes or hangs")
    if float(pre_stats.get("bitmap_cvg", "0%").rstrip("%")) <= 0:
        raise RuntimeError("preflight reported no AFL-instrumented feedback")
    check_smoke(CAMPAIGN / "preflight-smoke.json")
    check_smoke(CAMPAIGN / "postrun-smoke.json")
    replay = load_json(CAMPAIGN / "replay-summary.json")
    queue_count = sum(1 for p in (CAMPAIGN / "queue").iterdir() if p.is_file() and not p.name.startswith("."))
    if replay.get("samples_total") != queue_count:
        raise RuntimeError(f"queue replay does not cover all inputs: {replay.get('samples_total')} / {queue_count}")
    if (replay.get("target_started") != queue_count or
            replay.get("target_alive_after_input") != queue_count or
            replay.get("transport_results") != {"ok": queue_count}):
        raise RuntimeError("queue replay found an unexpected Apache exit or transport failure")
    replay_records = replay.get("records", [])
    if len(replay_records) != queue_count or any(
        not row.get("target_started") or not row.get("target_alive_after_input") or
        row.get("target_exit_code_after_cleanup") != 0 or row.get("transport_error") is not None
        for row in replay_records
    ):
        raise RuntimeError("a queue sample did not start, survive input, and exit cleanly after cleanup")
    hang_replay = load_json(CAMPAIGN / "hangs-replay-summary.json")
    hang_sample_count = sum(1 for p in (CAMPAIGN / "replayable-hangs").iterdir()
                            if p.is_file() and not p.name.startswith("."))
    if formal_hangs != hang_sample_count or hang_replay.get("samples_total") != formal_hangs:
        raise RuntimeError("AFLNet hang classifications are not all covered by the dedicated replay")
    if (hang_replay.get("target_started") != formal_hangs or
            hang_replay.get("target_alive_after_input") != formal_hangs or
            hang_replay.get("response_frames") != 0 or
            hang_replay.get("transport_results") != {"ok": formal_hangs}):
        raise RuntimeError("AFLNet hang replay found a process-level failure rather than malformed non-HTTP/2 input")
    hang_records = hang_replay.get("records", [])
    if len(hang_records) != formal_hangs or any(
        row.get("preface_valid") or
        not row.get("response_starts_http1") or
        not str(row.get("response_prefix_text", "")).startswith("HTTP/1.1 400 Bad Request") or
        row.get("response_frame_types") != [] or
        not row.get("target_alive_after_input") or row.get("target_exit_code_after_cleanup") != 0
        for row in hang_records
    ):
        raise RuntimeError("AFLNet hang replay did not confirm an invalid preface, HTTP/1.1 400, no HTTP/2 frames, and clean process shutdown")
    for name in ("listener-closed.json", "replay-listener-closed.json"):
        if not load_json(CAMPAIGN / name).get("listener_closed"):
            raise RuntimeError(f"Apache target is still active: {name}")
    if "status: complete" not in (ROOT / "ACCEPTANCE.md").read_text(encoding="utf-8").lower():
        raise RuntimeError("ACCEPTANCE.md must record status: complete before packaging")
    cleanup_path = ROOT / "build-logs/image-cleanup.json"
    if not pre_clean:
        cleanup = load_json(cleanup_path)
        if not cleanup.get("image_absent_after"):
            raise RuntimeError("benchmark Docker image cleanup was not verified")
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
            archive.write(path, Path("Apache-HTTP2-2.4.71") / path.relative_to(ROOT))
    with zipfile.ZipFile(ZIP) as archive:
        bad = archive.testzip()
        if bad:
            raise RuntimeError(f"ZIP CRC check failed: {bad}")
        names = set(archive.namelist())
        if any("基准化经验库" in name for name in names):
            raise RuntimeError("central experience library must not be included in protocol delivery")
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
    except (OSError, RuntimeError, ValueError, zipfile.BadZipFile, KeyError) as exc:
        print(f"package validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
