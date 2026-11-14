#!/usr/bin/env python3
import json
import pathlib
import re
import sys
from datetime import datetime

root = pathlib.Path(sys.argv[1])
duration = int(sys.argv[2])
exit_code = int(sys.argv[3])
log = (root / "run.log").read_text(errors="replace")
times = dict(line.split("=", 1) for line in (root / "run-times.txt").read_text().splitlines() if "=" in line)
done = re.findall(r"Done\s+(\d+)\s+runs\s+in\s+([0-9.]+)\s+second", log)
stats = {}
for key, value in re.findall(r"stat::([a-zA-Z0-9_]+):\s*([^\n]+)", log):
    stats[key] = value.strip()
final = re.findall(r"#(\d+)\s+DONE\s+cov:\s*(\d+)\s+ft:\s*(\d+).*?exec/s:\s*(\d+)", log)
corpus_files = [p for p in (root / "corpus").iterdir() if p.is_file()]
artifacts = [p.name for p in (root / "artifacts").iterdir() if p.is_file()]
asan_markers = sorted(set(re.findall(r"ERROR: AddressSanitizer: [^\n]+", log)))
ubsan_markers = sorted(set(re.findall(r"runtime error: [^\n]+", log)))
start = datetime.fromisoformat(times["start_utc"].replace("Z", "+00:00"))
end = datetime.fromisoformat(times["end_utc"].replace("Z", "+00:00"))
report = {
    "implementation": "libssh",
    "version": "0.12.2",
    "target": "ssh_server_fuzzer (upstream)",
    "scope": "SSH server parsing/state machine in-process over socketpair; no TCP listener",
    "engine": "LLVM libFuzzer",
    "sanitizers": ["ASan", "UBSan"],
    "requested_duration_seconds": duration,
    "observed_wall_seconds": round((end - start).total_seconds(), 3),
    "exit_code": exit_code,
    "complete": exit_code == 0 and bool(done) and (end - start).total_seconds() >= duration * 0.95,
    "runs": int(done[-1][0]) if done else None,
    "libfuzzer_reported_seconds": float(done[-1][1]) if done else None,
    "final_libfuzzer_counters": {
        "runs": int(final[-1][0]), "cov": int(final[-1][1]), "features": int(final[-1][2]), "exec_per_second": int(final[-1][3])
    } if final else None,
    "libfuzzer_stats": stats,
    "corpus_file_count": len(corpus_files),
    "corpus_bytes": sum(p.stat().st_size for p in corpus_files),
    "artifact_files": artifacts,
    "asan_errors": asan_markers,
    "ubsan_errors": ubsan_markers,
}
(root / "metrics.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
print(json.dumps(report, indent=2, ensure_ascii=False))
