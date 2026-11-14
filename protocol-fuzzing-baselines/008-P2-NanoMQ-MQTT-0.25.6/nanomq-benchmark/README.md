# NanoMQ MQTT/TCP AFLNet baseline

This package builds NanoMQ 0.25.6 with AFLNet's `afl-gcc` instrumentation in
both NanoMQ and its pinned NanoNNG submodule. The benchmark scope is one
foreground broker process, plain MQTT/TCP on `127.0.0.1:1883`, anonymous access,
and MQTT 3.1.1/5.0. TLS, WebSocket, HTTP API, persistence, clustering, and
bridging are outside this baseline.

The source revision and archive hashes are locked in `source/` and recorded in
`results/build/build-lock.txt`. The fixed seed corpus is generated from
`prepare_seeds.py`; the MQTT request-boundary and response-state adapter is in
`fuzzer/`.

Build and validate with Docker installed:

```sh
./build.sh
docker run --rm -v "$PWD/results:/work/results" \
  nanomq-mqtt-aflnet:0.25.6 -lc '/work/validate.sh'
```

Run the formal 30-minute campaign after the preflight passes:

```sh
docker run --rm -v "$PWD/results:/work/results" \
  nanomq-mqtt-aflnet:0.25.6 -lc '/work/run.sh /work/results/mqtt-30m 1800s'
```

The fuzzer and broker run in the same isolated container network namespace, so
no host ports are published. The preflight validates application-level
CONNECT/CONNACK readiness, six publish/subscribe flows, actual C-target
instrumentation, nonzero fuzz execution, and MQTT response states before the
long campaign. AFLNet's `-D` startup wait is 500,000 microseconds by default to
give the freshly started broker time to bind before each replay; override it
with `AFLNET_STARTUP_US` only after measuring the target's startup. Results
distinguish target code coverage from protocol state feedback and state the
limits of each metric.

The formal run and its limitations are summarized in
[`results/ACCEPTANCE.md`](results/ACCEPTANCE.md). The campaign completed its
time budget but did not finish a queue cycle and reported 47.26% stability;
treat it as a low-stability exploratory baseline.
