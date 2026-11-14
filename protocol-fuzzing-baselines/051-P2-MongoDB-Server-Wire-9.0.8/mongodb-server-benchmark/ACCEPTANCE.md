# MongoDB Server 9.0.8 — acceptance record

## Identity and scope

- Protocol: MongoDB Wire Protocol, OP_MSG.
- Target: MongoDB Server 9.0.8, official linux/amd64 Docker image.
- MongoDB build Git version: `115a0fe2dcd8edd5bacd4557bd2e741a8e080665`.
- Image manifest digest: `sha256:ff6cea7aa40c3ee44be503ed11f817928239d660b3927c79df4a1405e0923c1c`.
- Release date: 2026-11-10; official release notes are linked in `source-lock.json`.
- Fuzzer: AFLNet ProFuzzBench snapshot `0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732`; archive SHA-256 is in `source-lock.json`.
- Feedback: uninstrumented release binary, AFLNet `-n`, protocol response-state feedback. The helper bitmap is not MongoDB source coverage.
- Scope: unauthenticated standalone OP_MSG over TCP; TLS, auth, compressed/legacy opcodes, replica sets, sharding, and unseeded command families are excluded.
- State reset: stop `mongod`; create a new empty WiredTiger dbPath on tmpfs for each input.

## Validation results

### Formal campaign

- Host kernel: `7.2.15+kali-amd64`; the official binary was first checked against the runtime kernel before fuzzing.
- Wall interval: `2026-11-12T03:48:40Z`–`2026-11-12T04:18:42Z` (about 1,802 seconds). The container exited `0`, `OOMKilled=false`; the timer wrote `deadline_reached=1`, AFLNet handled `SIGINT`, and no `incomplete` marker was present.
- AFLNet statistics: 861 executions, 24 total response-state paths, 17 found paths, one completed cycle, 100% stability, zero unique crashes, and zero unique hangs. Peak RSS was 94 MiB.
- `bitmap_cvg=0.00%` is the helper bitmap only. MongoDB Server is an uninstrumented official release binary; this value is not MongoDB source coverage.
- The raw AFL queue contains 24 files; AFLNet replayable queue contains 24 files; new-IPSM replayable queue contains 19 files.

### Queue replay

- 67 samples were replayed against a new MongoDB process and empty WiredTiger directory per sample: 24 raw TCP streams, 24 length-prefixed replayable messages, and 19 new-IPSM paths.
- The samples produced 231 responses: 132 successful replies, 96 MongoDB error replies, and 3 replies that the profile parser could not classify. Every per-sample `mongod` process then stopped with exit code `0`.
- 40 samples had a receive event: 32 server connection closes and 8 bounded response timeouts. These are request-level outcomes, not AFLNet process crash/hang counts. The per-sample logs contained no fatal assertion, segmentation-fault, or panic signature.

### Protocol smoke

- Before and after fuzzing, three fresh-process repetitions over five valid command flows each returned 36 successful OP_MSG replies. Every reply matched its request ID and carried `ok: 1`.
- Both smoke summaries confirm all MongoDB listeners closed after their processes stopped.

Raw `fuzzer_stats`, `plot_data`, the queue and replay logs, container exit evidence, build identity, and smoke transcripts are retained under `results/`. `source-checksums.sha256` covers the pinned fuzzer snapshot, patches, adapter, seeds, and target lifecycle helpers. Scope limitations in this file still apply; the results do not claim full MongoDB command coverage or MongoDB source-code coverage.

### Docker cleanup

- After validating the delivery ZIP and its internal manifest, removed the three MongoDB benchmark containers, the profile image `mongodb-server-aflnet-bench:9.0.8`, and the pinned target image `mongo:9.0.8`.
- A post-cleanup inventory found no MongoDB benchmark containers or those two image tags. The Docker daemon still reports other projects' images and shared BuildKit cache; those were not part of this protocol's cleanup.
