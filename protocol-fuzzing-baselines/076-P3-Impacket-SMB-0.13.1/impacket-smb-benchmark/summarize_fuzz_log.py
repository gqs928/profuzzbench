#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path

text = Path(sys.argv[1]).read_text(errors="replace")
requested = int(sys.argv[2])
code = int(sys.argv[3])
corpus = Path(sys.argv[4])
done = re.findall(r"Done\s+(\d+)\s+runs?\s+in\s+([0-9.]+)\s+second", text)
snapshots = re.findall(r"(?:#\d+\s+)?(?:DONE|INITED).*?cov:\s*(\d+)\s*ft:\s*(\d+)", text)
executed = re.findall(r"stat::number_of_executed_units:\s*(\d+)", text)
new_units = re.findall(r"stat::new_units_added:\s*(\d+)", text)
peak_rss = re.findall(r"stat::peak_rss_mb:\s*(\d+)", text)
markers = [marker for marker in (
    "Uncaught Python exception", "ERROR: libFuzzer", "SUMMARY: libFuzzer",
    "ABORTED", "AddressSanitizer", "Traceback (most recent call last)",
) if marker in text]
corpus_files = sum(1 for item in corpus.iterdir() if item.is_file()) if corpus.exists() else 0
metrics = {
    "backend": "Atheris 3.1.0 / LLVM libFuzzer",
    "target": "Impacket 0.13.1 SMB2/SMB3 packet headers, command structures, selected negotiate/create contexts and transform headers",
    "requested_seconds": requested,
    "libfuzzer_done": {"executed_units": int(done[-1][0]), "seconds": float(done[-1][1])} if done else None,
    "final_stats": {
        "executed_units": int(executed[-1]) if executed else None,
        "new_units_added": int(new_units[-1]) if new_units else None,
        "python_coverage_edges": int(snapshots[-1][0]) if snapshots else None,
        "features": int(snapshots[-1][1]) if snapshots else None,
        "peak_rss_mb": int(peak_rss[-1]) if peak_rss else None,
        "saved_corpus_files": corpus_files,
    },
    "exit_code": code,
    "failure_markers": markers,
    "metrics_note": "Atheris/libFuzzer native progress and Python bytecode coverage are reported as emitted. AFLNet stability/bitmap and server readiness/listener/replay fields do not apply to this in-process parser target.",
}
print(json.dumps(metrics, indent=2))
