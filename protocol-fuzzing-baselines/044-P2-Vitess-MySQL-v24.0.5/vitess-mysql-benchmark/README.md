# Vitess MySQL Classic benchmark profile

This profile targets the MySQL Classic listener on Vitess v24.0.5, pinned to the official `vitess/vttestserver:v24.0.5-mysql84` image digest. The official vttestserver runs the Vitess components in one container. The profile creates one unsharded keyspace and sends SQL wire traffic to vtgate; it does not fuzz topology gRPC, tablet-control, or backend MySQL endpoints.

Vitess sends the MySQL greeting before the client request. The loopback-only authentication proxy creates a fresh root-authenticated upstream session for every testcase, then forwards AFLNet's MySQL command packet stream. This keeps the handshake out of the mutation stream while testing vtgate's MySQL query path. The profile uses network-only MySQL response-state feedback; AFLNet bitmap is not Vitess source coverage.

## Build and run

```sh
./build-aflnet.sh
./start-server.sh  # keep this terminal open
python3 protocol_smoke.py --port 14002
./fuzz.sh results/vitess-mysql-30m 1800
python3 replay_queue.py results/vitess-mysql-30m 14002
python3 triage_hangs.py results/vitess-mysql-30m --port 14002
python3 protocol_smoke.py --port 14002
./stop-server-and-remove-image.sh
```

The formal run uses a fresh Vitess server and read-oriented `COM_QUERY` corpus. Recovery checks compare vtgate SQL readiness and vtcombo status; only this profile container may be restarted. Replay records each sample's connection, response, close, and timeout outcomes. `ACCEPTANCE.md` records campaign timing, fuzzer counters, post-run smoke, replay, lifecycle events, and limitations. The shared framework experience library remains outside this protocol package.
