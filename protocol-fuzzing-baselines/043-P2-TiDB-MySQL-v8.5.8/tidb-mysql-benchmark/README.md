# TiDB MySQL protocol baseline

This profile targets the TiDB SQL endpoint over the MySQL Classic protocol. It pins the newest released stable LTS version verified on 2026-11-10: **v8.5.8**. PingCAP documents self-managed TiDB as a distributed system requiring the TiDB SQL layer plus PD and TiKV; the profile starts one official v8.5.8 container for each component on loopback host networking. Startup records each component image digest and checks the running TiDB binary with `/tidb-server -V` before fuzzing. For this image, the SQL port is set with the `-P=4000` flag.

TiDB speaks a server-first MySQL protocol. The local proxy performs a fresh upstream greeting/authentication exchange as `root` (default empty password), then forwards AFLNet's `COM_QUERY` packets unchanged. This keeps per-test sessions isolated and exposes SQL response states; authentication itself is validated by smoke tests and is outside the fuzzed input stream.

AFLNet runs in network-only response-state mode (`-n -E`); the official database containers are not compiler-instrumented, so `bitmap_cvg` is not source coverage. Read-only query seeds are used to avoid persistent data mutation.

## Build and run

```sh
./build-aflnet.sh
./start-server.sh  # keep this terminal open; use another terminal for the commands below
python3 protocol_smoke.py --port 14001
./fuzz.sh results/tidb-mysql-30m 1800
python3 replay_queue.py results/tidb-mysql-30m 14001
python3 triage_hangs.py results/tidb-mysql-30m --port 14001
python3 protocol_smoke.py --port 14001
```

After verifying this independent ZIP and its SHA-256, `./stop-server-and-remove-image.sh` removes only the three containers and official images used by this profile. The shared benchmark experience library is maintained outside this package.
