# VerneMQ MQTT 2.2.1 benchmark acceptance

## Target and scope

- Target: upstream VerneMQ 2.2.1, single-node broker, MQTT 3.1.1 and MQTT 5.0 over TCP on loopback.
- Source archive SHA-256 and pinned build/runtime dependencies are recorded in `source/SHA256SUMS` and `results/build/build-lock.txt`. The actual image ID is recorded in `results/build/image-id.txt` and `results/mqtt-30m/image-id.txt`.
- The target runs on Erlang BEAM. AFLNet's C forkserver/bitmap is supplied by a separate lifecycle helper; `bitmap_cvg`, `unique_crashes`, and `unique_hangs` therefore describe that helper path and are not VerneMQ code coverage or broker crash counts. The broker-facing feedback is the MQTT response-state graph.

## Preflight and service checks

- The 60-second MQTT/TCP AFLNet preflight passed and produced a nonempty response graph and fuzzer stats.
- The post-campaign health probe passed. Six real publish/subscribe smoke flows passed across MQTT 3.1.1 and MQTT 5.0 (three repetitions each); SUBACK and forwarded PUBLISH responses were checked. Full details and response hashes are in `mqtt-30m/service-smoke/service-smoke.json`.

## Formal campaign

- Elapsed: 1,800 seconds; wrapper exit code 124 is the expected `timeout` expiry for the requested 1,800-second window.
- AFLNet stats: 3,806 executions, 5 total paths, 0 variable paths, 100.00% helper bitmap stability, 0.00% helper bitmap coverage, and 0 helper-reported crashes/hangs. These helper counters are not target-code metrics.
- The target response graph contains `0 -> 2000 -> 109 -> 103 -> 111 -> 113`: successful MQTT CONNECT/CONNACK followed by SUBACK, PUBLISH, UNSUBACK and PINGRESP response states.
- The broker remained healthy after the campaign and completed the post-run smoke.

## Interpretation and limitations

This is an accepted protocol-state baseline for MQTT 3.1.1/5.0 in the profile above. It does not claim Erlang source coverage, absence of VerneMQ defects, TLS/WebSocket/cluster coverage, or behavior under persistence and external authentication. The helper's zero bitmap/crash/hang values must not be interpreted as target coverage or target defect absence.

## Evidence

`results/mqtt-30m/` preserves the raw AFLNet output, response graph, exact timestamps, wrapper status, startup/plugin logs, broker health, and smoke transcripts. `results/preflight/` preserves the successful 60-second preflight. `results/build/` records the image identity, source/dependency lock, instrumentation count, binary/source hashes, and build log.
