# VerneMQ 2.2.1 MQTT/TCP baseline

This profile builds VerneMQ 2.2.1 from a pinned upstream source archive and runs one isolated broker on loopback with anonymous MQTT/TCP access. The container ACL permits test clients to read and write all topics so the smoke flow can verify actual publish/subscribe forwarding. Startup explicitly enables VerneMQ's bundled `vmq_acl` plugin through a local Erlang RPC after the listener is ready; the single-node release otherwise leaves its configured user-plugin list inactive. Its declared scope is MQTT 3.1.1 and 5.0. TLS, WebSocket, clustering, persistence behavior, HTTP APIs, and external authentication plugins are outside the profile.

The request framing and response-state adapter is AFLNet's MQTT adapter. Real VerneMQ responses form the protocol state graph. Because the broker runs on Erlang BEAM, the AFLNet forkserver uses a separately instrumented lifecycle helper; its bitmap, crash, and hang counters do not measure VerneMQ code. The run checks broker readiness and MQTT health before and after fuzzing and labels these signals separately.

Build, validate, and run the 30-minute campaign with Docker:

```sh
./build.sh
docker run --rm --network none -v "$PWD/results:/work/results" vernemq-mqtt-aflnet:2.2.1 -lc '/work/validate.sh'
docker run --rm --network none -v "$PWD/results:/work/results" vernemq-mqtt-aflnet:2.2.1 -lc '/work/run.sh /work/results/mqtt-30m 1800s'
./package.sh
```

The independent ZIP includes the source archive, dependency/runtime lock, smoke flows, preflight, response graph, and formal run. The shared framework experience library is maintained separately.
