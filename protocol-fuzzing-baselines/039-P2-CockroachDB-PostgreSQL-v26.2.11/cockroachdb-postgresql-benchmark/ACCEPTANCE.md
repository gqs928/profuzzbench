# CockroachDB v26.2.11 PostgreSQL-wire acceptance record

- Official target: `cockroachdb/cockroach:v26.2.11`, OCI index digest `sha256:811e5001de2f003ca4539b03853d98e1fd79f70bf929393b17a645673f8d5f47`.
- Formal AFLNet duration: **1,801 active seconds** (requested 1,800), exit status 0.
- Results: 3,441 executions, 36 total response-state paths (27 discovered paths), 100% stability, 0 crash candidates, 11 AFLNet hang candidates. `bitmap_cvg=0%` is not source coverage because this is a black-box network-state run.
- Queue replay: 36/36 inputs connected, no replay socket errors, 596 backend frames, 67 ReadyForQuery messages, 19 SQL error responses, 3 peer resets and 18 idle read timeouts.
- Hang triage: all 11 saved hang candidates closed with a PostgreSQL-wire connection reset on isolated replay; the official server remained running, and a fresh `SELECT 1` smoke test then completed with one row, no SQL error, and ReadyForQuery. These are protocol-level connection closes / incomplete or malformed requests, not confirmed server crashes or persistent hangs.
- Corpus note: the seed generator placed `manifest.json` inside `seeds/`, so AFLNet imported one metadata file as an additional malformed input (9 initial files: 8 wire seeds plus metadata). This did not alter the eight valid protocol seeds; the unexpected close was observed during replay. The other four profiles in this batch keep corpus metadata outside the AFLNet seed directory.

The listener binds to loopback only. The single-node cluster uses the vendor's insecure test mode, so it is intended only for this local isolated benchmark.
