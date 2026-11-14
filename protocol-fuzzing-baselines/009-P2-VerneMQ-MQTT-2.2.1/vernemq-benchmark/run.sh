#!/usr/bin/env bash
set -u

OUTDIR="${1:-/work/results/mqtt-30m}"
DURATION="${2:-1800s}"
if [[ -e "${OUTDIR}" ]] && [[ -n "$(find "${OUTDIR}" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null)" ]]; then
  echo "Output directory is nonempty: ${OUTDIR}. Choose a fresh path." >&2
  exit 2
fi
mkdir -p "${OUTDIR}"
test -s /work/results/build/image-id.txt
cp /work/results/build/image-id.txt "${OUTDIR}/image-id.txt"

export ERL_FLAGS='+S 2:2 +SDcpu 1 +SDio 1 +A 2'
VERNEMQ=/opt/vernemq/bin/vernemq
"${VERNEMQ}" start >"${OUTDIR}/vernemq-start.log" 2>&1
cleanup() {
  "${VERNEMQ}" stop >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

READY=0
for _ in $(seq 1 120); do
  if "${VERNEMQ}" ping >/dev/null 2>&1 && python3 /work/wait_mqtt.py --host 127.0.0.1 --port 1883 --timeout 2; then
    READY=1
    break
  fi
  sleep 1
done
if [[ "${READY}" -ne 1 ]]; then
  echo "VerneMQ MQTT CONNECT/CONNACK readiness check failed" >&2
  cat "${OUTDIR}/vernemq-start.log" >&2
  exit 1
fi

# The single-node release starts with its SWC user-plugin manager empty even
# though plugins.vmq_acl is configured. Explicitly enable the bundled ACL
# plugin so anonymous test clients can subscribe to the smoke/fuzz topics.
erl -name baseline-bootstrap@127.0.0.1 -hidden \
  -setcookie vernemq-benchmark-cookie -noshell \
  -eval 'Node = list_to_atom("VerneMQ@127.0.0.1"), case rpc:call(Node, vmq_plugin_mgr, enable_plugin, [vmq_acl, []]) of ok -> io:format("PASS: vmq_acl plugin enabled for this isolated single-node run~n"), halt(0); Error -> io:format(standard_error, "Could not enable vmq_acl: ~p~n", [Error]), halt(1) end.' \
  >"${OUTDIR}/plugin-bootstrap.log" 2>&1 || {
    cat "${OUTDIR}/plugin-bootstrap.log" >&2
    exit 1
  }
cat "${OUTDIR}/plugin-bootstrap.log"

python3 /work/service_smoke.py "${OUTDIR}/service-smoke"

date -u +%s > "${OUTDIR}/external-start-epoch.txt"
printf 'lifecycle_target=/work/aflnet-lifecycle (instrumented C forkserver helper)\n' > "${OUTDIR}/run-method.txt"
printf 'broker=VerneMQ 2.2.1 BEAM process; real MQTT responses feed AFLNet state feedback\n' >> "${OUTDIR}/run-method.txt"
printf 'plugin_bootstrap=vmq_acl explicitly enabled via local Erlang RPC after MQTT readiness\n' >> "${OUTDIR}/run-method.txt"
printf 'coverage_limit=bitmap/crash/hang counters belong to helper, not VerneMQ BEAM code\n' >> "${OUTDIR}/run-method.txt"
set +e
timeout --signal=INT --kill-after=30s "${DURATION}" \
  env AFL_NO_UI=1 AFL_SKIP_CPUFREQ=1 AFL_NO_AFFINITY=1 \
  /opt/aflnet/afl-fuzz -d -i /work/seeds -x /work/mqtt.dict \
    -o "${OUTDIR}/aflnet-out" -N tcp://127.0.0.1/1883 -P MQTT \
    -E -q 3 -s 3 -R -K -D 1000 -W 100 -w 100000 -m none -t 5000+ \
    -- /work/aflnet-lifecycle >"${OUTDIR}/aflnet.log" 2>&1
FUZZER_STATUS=$?
set -e
date -u +%s > "${OUTDIR}/external-end-epoch.txt"
printf '%s\n' "${FUZZER_STATUS}" > "${OUTDIR}/wrapper-exit-code.txt"

if "${VERNEMQ}" ping >/dev/null 2>&1 && python3 /work/wait_mqtt.py --host 127.0.0.1 --port 1883 --timeout 10; then
  printf 'mqtt_health=pass_after_campaign\n' > "${OUTDIR}/broker-health.txt"
else
  printf 'mqtt_health=failed_after_campaign\n' > "${OUTDIR}/broker-health.txt"
  echo "VerneMQ failed the post-campaign MQTT health check" >&2
  exit 1
fi
if [[ -f "${OUTDIR}/aflnet-out/fuzzer_stats" ]]; then
  grep -E '^(execs_done|paths_total|paths_found|variable_paths|stability|bitmap_cvg|unique_crashes|unique_hangs|cycles_done)[[:space:]]*:' \
    "${OUTDIR}/aflnet-out/fuzzer_stats" > "${OUTDIR}/fuzzer-summary.txt" || true
fi
if [[ "${FUZZER_STATUS}" -ne 124 && "${FUZZER_STATUS}" -ne 0 ]]; then
  echo "AFLNet exit status: ${FUZZER_STATUS}" >&2
  exit "${FUZZER_STATUS}"
fi
