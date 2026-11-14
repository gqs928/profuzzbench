# Superseded EMQX preflight diagnostics

`preflight-before-readiness-fix/` preserves the initial run that checked only whether TCP/1883 accepted a connection. AFLNet then reported no response states, and a later smoke retry showed that the listener could accept TCP before completing MQTT CONNECT/CONNACK. This is diagnostic evidence, not a successful baseline.

The current `wait_mqtt.py` readiness check requires a successful MQTT 3.1.1 CONNECT/CONNACK exchange. The authoritative smoke and state-graph preflight is in `results/preflight/`.
