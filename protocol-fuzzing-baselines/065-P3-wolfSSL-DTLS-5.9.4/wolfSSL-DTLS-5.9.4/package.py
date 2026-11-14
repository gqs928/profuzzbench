#!/usr/bin/env python3
"""Validate wolfSSL benchmark evidence and build the standalone protocol ZIP."""
from __future__ import annotations
import hashlib, json, sys, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CAMPAIGN = ROOT / "results" / "wolfssl-dtls-fuzz-30m-20261112"
DEST = ROOT.parent / "deliverables" / "12-protocol-baselines-2026-11-03-framework"
ZIP = DEST / "65-wolfSSL-DTLS-5.9.4.zip"
INCLUDE = [
    ".dockerignore", "ACCEPTANCE.md", "Dockerfile", "PACKAGE-MANIFEST.md",
    "README.md", "build.sh", "compose.yaml", "deadline_wrapper.py", "images.env",
    "package.py", "prepare-target.sh", "prepare_seeds.py", "protocol_smoke.py",
    "replay_queue.py", "run-benchmark.sh", "run.sh", "seeds-manifest.json",
    "source-lock.json", "verify_listener_closed.py", "version-check.c",
    "build-logs", "seeds", "source", "results/campaign-console.log",
    "results/wolfssl-dtls-fuzz-30m-20261112",
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

def main() -> int:
    for path in [ROOT / "ACCEPTANCE.md", ROOT / "PACKAGE-MANIFEST.md", ROOT / "README.md",
                 ROOT / "source-lock.json", ROOT / "build-logs/build.log",
                 ROOT / "build-logs/image-id.txt", ROOT / "source/wolfssl-5.9.4.zip",
                 CAMPAIGN / "fuzzer_stats", CAMPAIGN / "plot_data",
                 CAMPAIGN / "run-parameters.txt", CAMPAIGN / "fuzzer-deadline.json",
                 CAMPAIGN / "preflight-smoke.json", CAMPAIGN / "replay-validation/replay-summary.json",
                 CAMPAIGN / "postrun-smoke.json", CAMPAIGN / "listener-closed.json"]:
        require(path)
    lock = json.loads((ROOT / "source-lock.json").read_text(encoding="utf-8"))
    source_digest = hashlib.sha256((ROOT / lock["target"]["source_archive"]).read_bytes()).hexdigest()
    if source_digest != lock["target"]["source_sha256"]:
        raise RuntimeError("wolfSSL source archive SHA-256 mismatch")
    deadline = load_json(CAMPAIGN / "fuzzer-deadline.json")
    if not deadline.get("deadline_reached") or deadline.get("stop_method") not in ("SIGINT", "SIGTERM"):
        raise RuntimeError(f"formal campaign did not reach its bounded deadline: {deadline}")
    stats = parse_stats(CAMPAIGN / "fuzzer_stats")
    runtime = int(stats.get("last_update", "0")) - int(stats.get("start_time", "0"))
    # AFLNet may write its final stats one second after the deadline signal;
    # the supervisor JSON is the authoritative 1,800-second timer record.
    if runtime not in (1800, 1801):
        raise RuntimeError(f"AFLNet stats span is outside the 1,800-second deadline window: {runtime}")
    if int(stats.get("unique_crashes", "-1")) != 0 or int(stats.get("unique_hangs", "-1")) != 0:
        raise RuntimeError("formal campaign reports crashes or hangs")
    for name in ("preflight-smoke.json", "postrun-smoke.json"):
        smoke = load_json(CAMPAIGN / name)
        if smoke.get("passes") != 3 or not smoke.get("handshakes_complete") or not smoke.get("echoes_received"):
            raise RuntimeError(f"DTLS pre/post smoke failed: {name}: {smoke}")
    replay = load_json(CAMPAIGN / "replay-validation/replay-summary.json")
    if not replay.get("validation_passed"):
        raise RuntimeError(f"queue replay validation failed: {replay}")
    closed = load_json(CAMPAIGN / "listener-closed.json")
    if not closed.get("listener_closed"):
        raise RuntimeError(f"target listener/process was not stopped: {closed}")
    acceptance = (ROOT / "ACCEPTANCE.md").read_text(encoding="utf-8").lower()
    if "status: complete" not in acceptance:
        raise RuntimeError("ACCEPTANCE.md must record status: complete before packaging")
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
            archive.write(path, Path("wolfSSL-DTLS-5.9.4") / path.relative_to(ROOT))
    with zipfile.ZipFile(ZIP) as archive:
        bad = archive.testzip()
        if bad:
            raise RuntimeError(f"ZIP CRC check failed: {bad}")
        names = set(archive.namelist())
        if any("基准化经验库" in name for name in names):
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
    except (OSError, RuntimeError, ValueError, zipfile.BadZipFile, KeyError) as exc:
        print(f"package validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
