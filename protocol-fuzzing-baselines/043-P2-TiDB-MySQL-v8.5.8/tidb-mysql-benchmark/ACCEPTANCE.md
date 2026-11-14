# TiDB v8.5.8 MySQL Classic baseline acceptance

## Target and scope

- TiDB self-managed v8.5.8, the highest released stable LTS version shown in the official release index checked on 2026-11-10: https://docs.pingcap.com/releases/tidb-self-managed/ . Release notes: https://docs.pingcap.com/tidb/stable/release-8.5.8/ .
- The running `/tidb-server -V` reported v8.5.8, commit `8b857efa20363d50a8fa2ea7dd9809a85a61b115`. The PD, TiKV and TiDB image digests are recorded in `source-lock.json` and `build/target-version-runtime.txt`.
- One official v8.5.8 container per PD/TiKV/TiDB component used loopback host networking. A local auth proxy opens a new upstream `root` session for each testcase and forwards MySQL Classic `COM_QUERY` bytes unchanged. Authentication is smoke-tested and excluded from the fuzzed stream.
- AFLNet source: `0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732`; mode: network-only MySQL response-state feedback (`-n -E`); binary SHA-256: `34731bc57f0e4aabb497b47839e049883cffe08dff1d8a99f3ad4a7464811dba`. The database images are not compiler-instrumented, so `bitmap_cvg=0%` is not source coverage.

## Formal run

- Requested 1,800 active seconds; completed 1,801 active seconds in 1,824 wall seconds, exit status 0.
- AFLNet recorded 5,247 executions, 283 total response-state paths (275 discovered), 0 variable paths, 100% stability, 0 unique crashes, 2 unique hang candidates and `cycles_done=0` (the first queue cycle did not finish).
- The successful 60-second preflight recorded 294 executions, 22 paths, 100% stability, 0 crashes and 0 hangs. Before formal fuzzing, a startup attempt exposed two profile issues: TiDB v8.5.8 uses `-P=4000` for the SQL port, and the MySQL response-state adapter needs synthetic initial state 0 because the proxy consumes greeting/authentication. Both were corrected; the parser test asserts state 0 and the fixed preflight passed.

## Replay and health checks

- Queue replay: 283/283 connected and all received non-empty responses. It collected 170,100 response bytes in 7,670 MySQL packets: 92 OK, 613 error, 1,908 EOF and 4,882 result-header packets. There were 0 connect errors, 0 send errors, 2 receive resets after response bytes, 118 peer closes and 163 bounded 350 ms idle-read timeouts. Per-sample results are in `results/tidb-30m/queue-replay.json`.
- Both saved hang candidates connected and received two MySQL error packets (122 response bytes) before an idle timeout; neither reproduced a persistent hang. See `results/tidb-30m/hang-triage.json`.
- `SELECT 1` smoke tests passed after the formal run and after replay.
- Docker events show two explicit `server-recover.sh` restarts at 14:11:10 and 14:12:02 UTC (each ended with exit code 0). Separately, TiDB logged `execute shutdown statement` at 14:19:42.142 UTC and received a termination signal at 14:19:43.144 UTC. The process exited cleanly and Docker's `unless-stopped` policy restarted it (`RestartCount=1`). TiDB documents that `SHUTDOWN` requires the `SHUTDOWN` privilege and stops the connected TiDB instance: https://docs.pingcap.com/tidb/stable/sql-statement-shutdown/ . Since the proxy authenticates as `root`, this administrative command is in scope and is classified separately from AFLNet crashes. Its triggering bytes were not retained in the final queue; no retained sample contains the literal `SHUTDOWN` token.
- TiDB logs contained 21 `connection running loop panic` entries. They are recorded as per-connection handler panic logs, separate from process-level crash counts. After replay, PD/TiKV/TiDB were running with restart counts 0/0/1 and `OOMKilled=false`; the final health probe and smoke passed. See `results/tidb-30m/server-health-evidence.txt`.

## Delivery and cleanup

The package contains the version lock and image digests, parser/seed tests, AFLNet build patches, proxy, smoke/replay tools, preflight, formal result, queue replay, hang triage and lifecycle evidence. Framework-oriented experience stays in the parent `基准化经验库.md`. After ZIP and SHA-256 validation, the exact three profile containers and three v8.5.8 image tags are removed by `stop-server-and-remove-image.sh`.
