#!/usr/bin/env python3
"""Validate LSQUIC evidence and build a standalone protocol ZIP."""
from __future__ import annotations

import hashlib
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PREFLIGHT = ROOT / "results/lsquic-preflight-60s-20261113"
CAMPAIGN = ROOT / "results/lsquic-fuzz-30m-20261113"
DEST = ROOT.parent / "deliverables/12-protocol-baselines-2026-11-03-framework"
ZIP = DEST / "69-LSQUIC-QUIC-4.11.1.zip"
CANDIDATE_ZIP = Path("/tmp/69-LSQUIC-QUIC-4.11.1-precleanup.zip")
IMAGE = "lsquic-aflnet-bench:v4.11.1"
INCLUDE = [
    ".dockerignore", "ACCEPTANCE.md", "Dockerfile", "PACKAGE-MANIFEST.md", "README.md",
    "build.sh", "build-info.sh", "compose.yaml", "deadline_wrapper.py", "images.env",
    "package.py", "patches/aflnet-quic.patch", "patches/expand-aflnet-map.py",
    "preflight-benchmark.sh", "protocol_smoke.py", "replay_queue.py", "run-benchmark.sh",
    "run.sh", "source/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz",
    "source/boringssl-10c780b1a3f67f9b8269502833808942979d5004.tar.gz",
    "source/ls-hpack-cf0f70dd10b352194c97448eb5d00b4aa484f531.tar.gz",
    "source/ls-qpack-91567706c41c0d97ab8dc576873ecd472d7869fa.tar.gz",
    "source/lsquic-v4.11.1.tar.gz", "source-lock.json",
    "toolchain-lock.json", "validate_seeds.py", "verify_listener_closed.py",
    "seeds", "build-logs", "results/lsquic-seed.sha256", "results/seed-validation.json",
    "results/lsquic-preflight-60s-20261113-console.log",
    "results/lsquic-fuzz-30m-20261113-console.log",
    "results/lsquic-preflight-60s-20261113", "results/lsquic-fuzz-30m-20261113",
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
    accepted = {"initial", "handshake", "retry", "version-negotiation"}
    checks = smoke.get("checks", [])
    if smoke.get("passes") != 3 or not smoke.get("all_responses_valid") or len(checks) != 3:
        raise RuntimeError(f"QUIC smoke failed: {path}")
    if any(
        row.get("request_packet_type") != "initial" or
        row.get("response_packet_type") not in accepted or
        not row.get("server_alive_after_request") or
        not row.get("server_exit_after_controlled_sigterm") or
        not row.get("listener_released")
        for row in checks
    ):
        raise RuntimeError(f"three valid Initial response and cleanup cycles were not verified: {path}")


def check_replay(summary_path: Path, sample_dir: Path, expected: int) -> None:
    summary = load_json(summary_path)
    files = sum(1 for path in sample_dir.iterdir()
                if path.is_file() and not path.name.startswith("."))
    records = summary.get("records", [])
    if summary.get("samples_total") != files or files != expected or len(records) != files:
        raise RuntimeError(f"replay coverage mismatch: {summary_path}")
    if any(not row.get("target_started") or not row.get("listener_released")
           for row in records):
        raise RuntimeError(f"some replay did not start and release its server: {summary_path}")
    if summary.get("listeners_released") != files:
        raise RuntimeError(f"not every replay released its UDP listener: {summary_path}")
    if sample_dir.name == "queue" and any(
        not row.get("target_alive_after_input") or not row.get("clean_sigterm_exit")
        for row in records
    ):
        raise RuntimeError(f"ordinary queue replay found an unexpected target exit: {summary_path}")


def main() -> int:
    candidate_mode = sys.argv[1:] == ["--candidate"]
    if len(sys.argv) > 1 and not candidate_mode:
        raise RuntimeError("usage: package.py [--candidate]")
    lock = load_json(ROOT / "source-lock.json")
    toolchain = load_json(ROOT / "toolchain-lock.json")
    hashes = [
        (ROOT / "source" / lock["source_archive"], lock["source_sha256"]),
        (ROOT / "source" / lock["boringssl_archive"], lock["boringssl_sha256"]),
        (ROOT / "source" / lock["aflnet_archive"], lock["aflnet_sha256"]),
        (ROOT / "source" / lock["submodules"]["src/liblsquic/ls-qpack"]["archive"],
         lock["submodules"]["src/liblsquic/ls-qpack"]["sha256"]),
        (ROOT / "source" / lock["submodules"]["src/lshpack"]["archive"],
         lock["submodules"]["src/lshpack"]["sha256"]),
        (ROOT / "patches/aflnet-quic.patch", lock["aflnet_patch_sha256"]),
        (ROOT / lock["aflnet_map_size_script"], lock["aflnet_map_size_script_sha256"]),
        (ROOT / "seeds/quic-v1-client-initial.bin", lock["seed_sha256"]),
    ]
    for path, expected in hashes:
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise RuntimeError(f"locked SHA-256 mismatch: {path.relative_to(ROOT)}")
    if toolchain.get("aflnet_map_size") != 262144:
        raise RuntimeError("toolchain lock differs from the accepted profile")
    seed_report = load_json(ROOT / "results/seed-validation.json")
    if not seed_report.get("valid") or not seed_report.get("datagram_atomic"):
        raise RuntimeError("QUIC seed validation failed")

    for path in (
        ROOT / "build-logs/docker-build.log", ROOT / "build-logs/image-id.txt",
        ROOT / "build-logs/build-info.txt", ROOT / "build-logs/image-cleanup.json",
        ROOT / "results/lsquic-seed.sha256",
        ROOT / "results/lsquic-preflight-60s-20261113-console.log",
        ROOT / "results/lsquic-fuzz-30m-20261113-console.log",
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

    for run, seconds in ((PREFLIGHT, 60), (CAMPAIGN, 1800)):
        deadline = load_json(run / "fuzzer-deadline.json")
        if not deadline.get("deadline_reached") or deadline.get("requested_duration_seconds") != seconds:
            raise RuntimeError(f"requested fuzzer deadline was not completed: {run}")
        stats = parse_stats(run / "fuzzer_stats")
        span = int(stats.get("last_update", "0")) - int(stats.get("start_time", "0"))
        elapsed = float(deadline.get("elapsed_seconds", -1))
        if abs(elapsed - seconds) > 1.0:
            raise RuntimeError(f"supervisor duration outside one-second tolerance: {elapsed}: {run}")
        if seconds == 1800 and not seconds <= span <= seconds + 5:
            raise RuntimeError(f"unexpected fuzzer stats writeout span {span} seconds: {run}")
        if seconds == 60 and not 55 <= span <= 65:
            raise RuntimeError(f"unexpected preflight stats span {span} seconds: {run}")
        if float(stats.get("bitmap_cvg", "0%").rstrip("%")) <= 0:
            raise RuntimeError(f"fuzzer received no target coverage feedback: {run}")
        check_smoke(run / "preflight-smoke.json")
        check_smoke(run / "postrun-smoke.json")
        if not load_json(run / "listener-closed.json").get("listener_closed"):
            raise RuntimeError(f"UDP listener remained open: {run}")
        queue = load_json(run / "replay-summary.json")
        check_replay(run / "replay-summary.json", run / "queue",
                     int(queue.get("samples_total", -1)))
        fuzz_stats = parse_stats(run / "fuzzer_stats")
        for dirname, key in (("hangs", "unique_hangs"),
                             ("crashes", "unique_crashes")):
            sample_dir = run / f"replayable-{dirname}"
            sample_dir.mkdir(parents=True, exist_ok=True)
            check_replay(run / f"{dirname}-replay-summary.json",
                         sample_dir, int(fuzz_stats.get(key, "0")))
        if not load_json(run / "replay-listener-closed.json").get("listener_closed"):
            raise RuntimeError(f"UDP listener remained open after sample replay: {run}")

    acceptance = (ROOT / "ACCEPTANCE.md").read_text(encoding="utf-8").lower()
    cleanup = load_json(ROOT / "build-logs/image-cleanup.json")
    if cleanup.get("image_tag") != IMAGE:
        raise RuntimeError("cleanup record refers to a different image")
    if candidate_mode:
        if "status: benchmark passed; packaging and image cleanup pending" not in acceptance:
            raise RuntimeError("candidate packaging requires a passed benchmark with finalization still pending")
        if cleanup.get("status") != "pending" or cleanup.get("image_absent_after"):
            raise RuntimeError("candidate package must honestly record image cleanup as pending")
    else:
        if "status: complete" not in acceptance:
            raise RuntimeError("ACCEPTANCE.md must say status: complete before final packaging")
        if not cleanup.get("image_absent_after"):
            raise RuntimeError("dedicated LSQUIC image is not verified absent")

    DEST.mkdir(parents=True, exist_ok=True)
    output_zip = CANDIDATE_ZIP if candidate_mode else ZIP
    if output_zip.exists():
        output_zip.unlink()
    files: set[Path] = set()
    for name in INCLUDE:
        path = ROOT / name
        if not path.exists():
            raise RuntimeError(f"declared package input missing: {name}")
        if path.is_file():
            files.add(path)
        else:
            files.update(item for item in path.rglob("*") if item.is_file())
    files = {path for path in files if "__pycache__" not in path.parts and path.suffix != ".pyc"}
    manifest = [
        f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(ROOT).as_posix()}"
        for path in sorted(files)
    ]
    root_name = "LSQUIC-QUIC-4.11.1"
    with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in sorted(files):
            archive.write(path, Path(root_name) / path.relative_to(ROOT))
        archive.writestr(f"{root_name}/MANIFEST.SHA256", "\n".join(manifest) + "\n")
    with zipfile.ZipFile(output_zip) as archive:
        bad = archive.testzip()
        if bad:
            raise RuntimeError(f"ZIP CRC check failed: {bad}")
        if any("基准化经验库" in name for name in archive.namelist()):
            raise RuntimeError("central experience library must be outside this protocol ZIP")
    digest = hashlib.sha256(output_zip.read_bytes()).hexdigest()
    output_zip.with_suffix(output_zip.suffix + ".sha256").write_text(
        f"{digest}  {output_zip.name}\n", encoding="ascii")
    print(f"PASS: {output_zip} ({output_zip.stat().st_size} bytes), SHA-256 {digest}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, zipfile.BadZipFile, KeyError) as exc:
        print(f"package validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
