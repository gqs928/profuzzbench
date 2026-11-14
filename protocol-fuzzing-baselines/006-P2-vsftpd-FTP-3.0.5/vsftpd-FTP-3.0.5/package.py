#!/usr/bin/env python3
"""Create a deterministic, self-contained vsftpd 3.0.5 baseline ZIP."""
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
    ".dockerignore", "Dockerfile", "README.md", "RESULTS.md", "build.sh",
    "run.sh", "postprocess.sh", "validate.sh", "validate.py",
    "replay_corpus.py", "package.py", "vsftpd.conf",
    "source-checksums.sha256", "source", "dictionary", "seeds", "results",
]
files = []
for relative in paths:
    candidate = root / relative
    if not candidate.exists():
        raise SystemExit(f"required package input is missing: {relative}")
    if candidate.is_dir():
        files.extend(path for path in sorted(candidate.rglob("*"))
                     if path.is_file() and "__pycache__" not in path.parts)
    else:
        files.append(candidate)

entries = sorted(set(files))
prefix = "vsftpd-FTP-3.0.5"
with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
    for path in entries:
        relative = path.relative_to(root).as_posix()
        info = zipfile.ZipInfo(f"{prefix}/{relative}", date_time=(1980, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = (0o100644 & 0xFFFF) << 16
        archive.writestr(info, path.read_bytes())

digest = hashlib.sha256(output.read_bytes()).hexdigest()
output.with_suffix(output.suffix + ".sha256").write_text(f"{digest}  {output.name}\n")
print(f"{output} {digest} {len(entries)} files")
