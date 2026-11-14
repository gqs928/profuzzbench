#!/usr/bin/env python3
import json, re, sys
from pathlib import Path
text=Path(sys.argv[1]).read_text(errors='replace')
requested=int(sys.argv[2]); code=int(sys.argv[3])
execs=re.findall(r"stat::number_of_executed_units:\s*(\d+)",text)
new=re.findall(r"stat::new_units_added:\s*(\d+)",text)
cov=re.findall(r"stat::number_of_covered_edges:\s*(\d+)",text)
features=re.findall(r"stat::number_of_features:\s*(\d+)",text)
progress=re.findall(r"#\d+\s+DONE\s+cov:\s*(\d+)\s+ft:\s*(\d+)",text)
done=re.findall(r"Done\s+(\d+)\s+runs?\s+in\s+([0-9.]+)\s+second",text)
markers=[x for x in ("ERROR: AddressSanitizer", "SUMMARY: AddressSanitizer", "ERROR: libFuzzer", "ABORTED", "runtime error:") if x in text]
metrics={"backend":"LLVM libFuzzer","target":"PJSIP upstream tests/fuzz/fuzz-sip.c:LLVMFuzzerTestOneInput","requested_seconds":requested,"libfuzzer_done":{"executed_units":int(done[-1][0]),"seconds":float(done[-1][1])} if done else None,"final_stats":{"executed_units":int(execs[-1]) if execs else None,"new_units_added":int(new[-1]) if new else None,"covered_edges":int(cov[-1]) if cov else (int(progress[-1][0]) if progress else None),"features":int(features[-1]) if features else (int(progress[-1][1]) if progress else None)},"exit_code":code,"failure_markers":markers,"metrics_note":"Native libFuzzer counters are reported as emitted; AFLNet stability/bitmap and server readiness/replay fields do not apply to this in-process harness."}
print(json.dumps(metrics,indent=2))
