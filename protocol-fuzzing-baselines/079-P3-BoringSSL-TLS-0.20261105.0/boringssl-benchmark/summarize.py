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
stats = {key: value.strip() for key, value in re.findall(r"stat::([a-zA-Z0-9_]+):\s*([^\n]+)", log)}
final = re.findall(r"#(\d+)\s+DONE\s+cov:\s*(\d+)\s+ft:\s*(\d+).*?exec/s:\s*(\d+)", log)
corpus_files = [p for p in (root / "corpus").iterdir() if p.is_file()]
artifacts = sorted(p.name for p in (root / "artifacts").iterdir() if p.is_file())
asan_markers = sorted(set(re.findall(r"ERROR: AddressSanitizer: [^\n]+", log)))
start = datetime.fromisoformat(times["start_utc"].replace("Z", "+00:00"))
end = datetime.fromisoformat(times["end_utc"].replace("Z", "+00:00"))
elapsed = (end - start).total_seconds()
report = {
    "implementation": "BoringSSL",
    "version": "0.20261105.0",
    "source_commit": "3dc4b63808921e914a3fb1fa61869abc3938781b",
    "target": "upstream fuzz/server.cc (server)",
    "scope": "TLS server handshake/state-machine parsing in-process; no TCP listener",
    "engine": "LLVM libFuzzer",
    "sanitizers": ["ASan"],
    "requested_duration_seconds": duration,
    "observed_wall_seconds": round(elapsed, 3),
    "exit_code": exit_code,
    "complete": exit_code == 0 and bool(done) and elapsed >= duration * 0.95,
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
}
(root / "metrics.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
print(json.dumps(report, indent=2, ensure_ascii=False))
