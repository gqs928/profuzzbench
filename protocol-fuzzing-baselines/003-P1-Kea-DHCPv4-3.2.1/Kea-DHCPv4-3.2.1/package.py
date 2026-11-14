#!/usr/bin/env python3
"""Package Kea DHCPv4 baseline evidence without the shared experience library."""

import hashlib
import sys
import zipfile
from pathlib import Path

root = Path(__file__).resolve().parent
if len(sys.argv) != 2:
    raise SystemExit("usage: package.py OUTPUT.zip")
output = Path(sys.argv[1]).resolve()
output.parent.mkdir(parents=True, exist_ok=True)

paths = [
    "Dockerfile", "Dockerfile.aflnet-overlay", "README.md", "RESULTS.md",
    "build.sh", "run.sh", "validate.py", "triage_hangs.py", "make_seeds.py", "package.py",
    "kea-target.sh", "kea.conf", "source-checksums.sha256",
    "patch-checksums.sha256", "aflnet-dhcp.patch", "aflnet-local-port.patch",
    "source", "seeds", "results/build/docker-build.log",
    "results/build/docker-build-final.log", "results/build/overlay-build.log",
    "results/build/build-lock.txt", "results/build/image-id.txt",
    "results/build/dpkg-versions.txt",
    "results/build/service-smoke.json", "results/build/smoke",
    "results/calibration/relay-smoke", "results/dhcp4-30m/run.json",
    "results/dhcp4-30m/fuzzer_stats", "results/dhcp4-30m/fuzzer-summary.txt",
    "results/dhcp4-30m/aflnet.log", "results/dhcp4-30m/aflnet-out/fuzzer_stats",
    "results/dhcp4-30m/aflnet-out/fuzz_bitmap", "results/dhcp4-30m/aflnet-out/ipsm.dot",
    "results/dhcp4-30m/aflnet-out/plot_data", "results/dhcp4-30m/aflnet-out/queue",
    "results/dhcp4-30m/aflnet-out/regions",
    "results/dhcp4-30m/aflnet-out/replayable-hangs",
    "results/dhcp4-30m/aflnet-out/replayable-crashes",
    "results/dhcp4-30m/triage",
]

files = []
for relative in paths:
    candidate = root / relative
    if not candidate.exists():
        raise SystemExit(f"required package input is missing: {relative}")
    if candidate.is_dir():
        files.extend(
            path for path in sorted(candidate.rglob("*"))
            if path.is_file() and "__pycache__" not in path.parts
        )
    else:
        files.append(candidate)

entries = sorted(set(files))
checksums = "".join(
    f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(root).as_posix()}\n"
    for path in entries
)
(root / "SHA256SUMS.txt").write_text(checksums)
entries.append(root / "SHA256SUMS.txt")
prefix = "Kea-DHCPv4-3.2.1"
with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
    for path in sorted(set(entries)):
        relative = path.relative_to(root).as_posix()
        info = zipfile.ZipInfo(f"{prefix}/{relative}", date_time=(1980, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        mode = 0o100755 if path.stat().st_mode & 0o111 else 0o100644
        info.external_attr = (mode & 0xFFFF) << 16
        archive.writestr(info, path.read_bytes())

digest = hashlib.sha256(output.read_bytes()).hexdigest()
output.with_suffix(output.suffix + ".sha256").write_text(f"{digest}  {output.name}\n")
print(f"{output} {digest} {len(set(entries))} files")
