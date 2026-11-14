#!/usr/bin/env bash
set -euo pipefail
OUT=${1:?usage: smoke.sh OUTDIR [PASSES]}
PASSES=${2:-3}
if [[ -e "$OUT" ]] && [[ -n $(find "$OUT" -mindepth 1 -maxdepth 1 -print -quit) ]]; then
  echo "smoke output directory must be empty: $OUT" >&2
  exit 2
fi
mkdir -p "$OUT"
status=0
for ((pass=1; pass<=PASSES; pass++)); do
  export BGPD_LOG_FILE="$OUT/bgpd-pass-${pass}.log"
  /bin/bash /opt/benchmark/start-bgpd.sh
  if python3 /opt/benchmark/bgp_smoke.py --host "${BGP_HOST:-127.0.0.1}" \
      --port "${BGP_PORT:-179}" --passes 1 \
      --output "$OUT/protocol-smoke-pass-${pass}.json"; then
    :
  else
    status=$?
  fi
  /bin/bash /opt/benchmark/stop-bgpd.sh
  [[ $status -eq 0 ]] || break
done
if [[ $status -eq 0 ]]; then
  python3 - "$OUT" "$PASSES" <<'PY'
import json,sys
from pathlib import Path
out=Path(sys.argv[1]); passes=int(sys.argv[2]); records=[]
for index in range(1, passes+1):
    source=out/f"protocol-smoke-pass-{index}.json"
    records.extend(json.loads(source.read_text(encoding="utf-8"))["passes"])
(out/"protocol-smoke.json").write_text(
    json.dumps({"passes":records},indent=2)+"\n",encoding="utf-8")
PY
fi
python3 - "${BGP_HOST:-127.0.0.1}" "${BGP_PORT:-179}" "$OUT/listener-closed.json" <<'PY'
import json,socket,sys
sock=socket.socket(); sock.settimeout(.25)
state='closed' if sock.connect_ex((sys.argv[1],int(sys.argv[2]))) else 'open'
sock.close()
open(sys.argv[3],'w').write(json.dumps({'listener_state':state},indent=2)+'\n')
if state != 'closed': raise SystemExit('BGP listener remained open after bgpd shutdown')
PY
chmod -R a+rX "$OUT"
[[ $status -eq 0 ]] || exit "$status"
echo "PASS: FRRouting BGP smoke; listener closed after shutdown"
