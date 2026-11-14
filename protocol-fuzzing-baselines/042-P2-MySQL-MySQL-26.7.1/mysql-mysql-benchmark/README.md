# MySQL Server MySQL protocol baseline

This package targets MySQL Server **26.7.1** through its MySQL Classic protocol endpoint. It pins the Oracle Container Registry image `container-registry.oracle.com/mysql/community-server:26.7.1`, verified on 2026-11-10.

Version evidence: [MySQL 26.7.1 release notes](https://dev.mysql.com/doc/relnotes/mysql/26.7/en/news-26-7-1.html) identify this as a Docker image security-patch release; the [MySQL Docker deployment guide](https://dev.mysql.com/doc/refman/26.7/en/docker-mysql-getting-started.html) names Oracle Container Registry as the Community Server image source. The Docker Hub tag `mysql:26.7.1` is not published, so the locked target uses the exact 26.7.1 OCR tag.

The implementation speaks a server-first protocol: the server greeting contains a per-connection salt needed to authenticate, so static client handshake seeds cannot reliably log in. A loopback-only Python proxy authenticates to the real server on each test connection, then forwards the MySQL request stream unmodified to that server. AFLNet mutates deterministic `COM_QUERY` requests and observes the server's real SQL wire responses. This isolates the SQL command path; authentication negotiation is checked by the smoke test and is not fuzzed.

AFLNet runs in network-only response-state feedback mode (`-n -E`); the official database image has no fuzzer instrumentation, so `bitmap_cvg` is not code coverage. Seeds are read-only and each test receives a fresh upstream connection to avoid cross-case transaction/session carryover.

## Build and run

```sh
./build-aflnet.sh
./start-server.sh  # keep this terminal open; use another terminal for the commands below
python3 protocol_smoke.py --port 14307
./fuzz.sh results/mysql-mysql-30m 1800
python3 replay_queue.py results/mysql-mysql-30m 14307
python3 protocol_smoke.py --port 14307
```

After verifying this delivery ZIP and its SHA-256, run `./stop-server-and-remove-image.sh` to remove only this profile's container and official image. Shared benchmark framework experience is maintained centrally outside this package.
