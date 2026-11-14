# dcm4che 5.35.2 — DICOM Upper Layer/TCP baseline

This profile targets the newest official complete dcm4che3 binary toolkit distribution containing `storescp`, version 5.35.2 as of 2026-11-12. The separate `dcm4che-core` Maven index has a 5.36.0 module entry dated 2026-11-09, but it is not a newer complete `storescp` toolkit; the profile does not mix module versions. The DICOM scope is the plaintext DICOM Upper Layer on a single TCP listener, including association setup, Verification C-ECHO, Storage C-STORE, and release/abort PDUs. TLS, DICOMweb, HL7, LDAP-backed configuration, and multi-node application workflows are excluded.

The pinned AFLNet snapshot already includes a DICOM request framer selected by `-P DICOM`. It splits the six-byte big-endian UL PDU header and length. Its stock response extractor emits only the first byte of each received buffer, so this profile replaces that response extractor with a narrow extension that preserves every complete PDU type and extracts DIMSE Command Field (0000,0100) from command PDVs. `dicom-parser-test.c` covers multi-PDU framing, C-ECHO response state, association-reject detail, and truncated-length classification.

The seed client should build a complete A-ASSOCIATE-RQ and C-ECHO/C-STORE session so each testcase begins from a valid application state. Each testcase resets the server process and receive directory; queue replay must apply the same reset and readiness contract. The JVM/target is not coverage-instrumented; AFLNet helper bitmap is not dcm4che source coverage.

## Build, run, and validate

```sh
./build.sh
docker compose --env-file images.env -f compose.yaml run --rm fuzz
```

After the formal run, replay saved raw queue streams with a fresh `storescp` JVM per sample, then run post-campaign protocol smoke:

```sh
docker compose --env-file images.env -f compose.yaml run --rm --entrypoint python3 fuzz \
  /opt/benchmark/replay_queue.py \
  /results/dcm4che-fuzz-30m-YYYYMMDD/queue \
  /results/dcm4che-fuzz-30m-YYYYMMDD/replay-validation
./post-smoke.sh /results/dicom-smoke-post-20261112
```

Version evidence, binary archive checksum, exact runtime image, and AFLNet patch hashes are in `source-lock.json`. Framework lessons belong only in the shared `deliverables/12-protocol-baselines-2026-11-03-framework/基准化经验库.md`, not this protocol's ZIP.
