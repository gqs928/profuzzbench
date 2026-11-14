# FerretDB MongoDB Wire Protocol benchmark

This profile targets the latest stable FerretDB production release (`v2.7.0`, to be verified against the official release and image metadata immediately before the run) over its MongoDB Wire Protocol TCP endpoint. FerretDB 2.x requires the PostgreSQL DocumentDB backend; the matching backend image in the official installation guide is `ghcr.io/ferretdb/postgres-documentdb:17-0.107.0-ferretdb-2.7.0`. The benchmark must pin both images by platform-specific digest and record their in-container version output.

The official FerretDB releases page still marks v2.7.0 as the latest release. The target and matched DocumentDB backend are pinned by their observed amd64 manifest digests; the builder is pinned to Debian Trixie snapshot `20261020T213255Z`. The Dockerfile uses the signed Debian snapshot over HTTP because the minimal base image has no root CA bundle at first; apt still verifies signed Release metadata and package hashes.

The seed corpus uses valid MongoDB OP_MSG requests with a `hello` handshake, read-only commands, and one isolated create/insert/find/delete sequence. Every testcase uses a fresh FerretDB process. The matched DocumentDB extension is initialized in PostgreSQL database `postgres`; `pg_cron` requires that database for scheduled extension jobs. Before each testcase, the launcher enumerates MongoDB database names from `documentdb_api_catalog.collections` and resets their collections through DocumentDB’s `drop_database` API, preserving extension objects and PostgreSQL system state. The parser must split messages from the 16-byte little-endian wire header and map actual OP_MSG response status into coarse, documented response states. The official Go target is not AFL-instrumented, so this profile runs AFLNet in `-n` mode with an explicit patch that queues an input when it discovers a new response-state sequence. `bitmap_cvg` measures only the AFL launcher/helper and must be zero or near zero; it is not FerretDB source coverage. Report retained response-state paths, replay results, and crashes separately from source-code coverage.

TLS and authentication, replica sets, sharding, change streams, sessions/transactions, MongoDB commands not accepted by FerretDB, and backend PostgreSQL protocol fuzzing are out of scope. The isolated profile sets `FERRETDB_AUTH=false` using the v2.7.0 `--[no-]auth` option so the corpus exercises unauthenticated MongoDB wire commands only. Preserve the FerretDB and DocumentDB versions as a matched pair.

## Acceptance flow

1. Verify release version, image digests, and the FerretDB binary's `--version` output.
2. Regenerate `seeds/` and confirm hashes against `seeds-manifest.json`.
3. Run parser unit tests and repeat a real hello/ping/CRUD wire exchange against fresh service state.
4. Run a short AFLNet smoke test, then one 30-minute formal campaign with CPU, memory, and network limits.
5. Replay the final queue with a fresh FerretDB/backend state per input, preserve protocol logs, result statistics, and image hashes, then build and checksum the standalone ZIP.
6. After package checks pass, remove only the benchmark image and the exact FerretDB/DocumentDB image IDs used for this run.

The aggregated baseline experience belongs in the central `基准化经验库.md`; this per-protocol package contains its own reproducible setup and evidence, not a separate experience entry.
