#!/usr/bin/env python3
"""Package open62541 OPC UA/TCP baseline evidence without shared experiences."""

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
    "Dockerfile", "README.md", "RESULTS.md", "build.sh", "run.sh",
    "make_seeds.py", "package.py", "fuzz_tcp_message.patch",
    "patch-checksums.sha256", "source-checksums.sha256", "source",
    "seeds", "results/build", "results/smoke",
    "results/first-attempt-timeout",
    "results/premerge-full-corpus-interrupted",
    "results/fork-partial-volatile",
    "results/opcua-30m/run.json", "results/opcua-30m/libfuzzer.log",
    "results/opcua-30m/corpus", "results/opcua-30m/artifacts",
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
(root / "SHA256SUMS.txt").write_text(checksums, encoding="utf-8")
entries.append(root / "SHA256SUMS.txt")
prefix = "open62541-OPC-UA-1.5.10"
with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
    for path in sorted(set(entries)):
        relative = path.relative_to(root).as_posix()
        info = zipfile.ZipInfo(f"{prefix}/{relative}", date_time=(1980, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        mode = 0o100755 if path.stat().st_mode & 0o111 else 0o100644
        info.external_attr = (mode & 0xFFFF) << 16
        archive.writestr(info, path.read_bytes())

digest = hashlib.sha256(output.read_bytes()).hexdigest()
output.with_suffix(output.suffix + ".sha256").write_text(f"{digest}  {output.name}\n", encoding="utf-8")
print(f"{output} {digest} {len(set(entries))} files")
