#!/usr/bin/env python3
"""Extract Go's native fuzz progress summaries without inventing AFL metrics."""
from __future__ import annotations

import json
import pathlib
import re
import sys

log_path = pathlib.Path(sys.argv[1])
out_path = pathlib.Path(sys.argv[2])
text = log_path.read_text(encoding="utf-8", errors="replace")
lines = [line.strip() for line in text.splitlines() if line.lstrip().startswith("fuzz:")]
exit_status = int(sys.argv[3]) if len(sys.argv) > 3 else None
summary = {
    "backend": "go test native fuzz",
    "target": "internal/wire.FuzzHeaderParser",
    "progress_lines": lines,
    "final_progress_line": lines[-1] if lines else None,
    "metrics_note": "Go native fuzz output has no AFLNet stability or bitmap_cvg fields; do not synthesize them.",
    "panic_or_failure_markers": [
        marker for marker in ("FAIL", "panic:", "fatal error:") if marker in text
    ],
}
match = re.search(r"execs:\s*([0-9]+)", lines[-1]) if lines else None
summary["final_execs"] = int(match.group(1)) if match else None
summary["fuzzer_exit_status"] = exit_status
out_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
