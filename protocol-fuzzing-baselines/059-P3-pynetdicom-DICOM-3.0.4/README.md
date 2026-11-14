# pynetdicom 3.0.4 — DICOM Upper Layer/TCP baseline

This profile targets the latest stable pynetdicom release verified on 2026-11-12 and its official `storescp` application. It covers plaintext DICOM Upper Layer on one TCP listener, including association negotiation, Verification C-ECHO, Storage C-STORE, and release. TLS, DICOMweb, HL7, LDAP-backed configuration, and multi-node workflows are excluded.

The package is pure Python and uses pydicom for data-set encoding. The runtime locks both PyPI wheel hashes and asserts both installed versions. AFLNet's upstream DICOM request parser splits the six-byte big-endian UL PDU header and length; the local response extension keeps every complete PDU type and extracts DIMSE Command Field (0000,0100) from command PDVs. A parser unit test covers multi-PDU framing, C-ECHO response state, association reject detail, and truncated-length classification. The build also applies a generic AFLNet network-endpoint parser fix: the upstream `-N` parser copies the argument without a terminating NUL, so the build rejects the image unless the patched parser accepts the same endpoint 64 consecutive times.

Seeds exercise A-ASSOCIATE-RQ, C-ECHO, and one-pixel Secondary Capture C-STORE. Each fuzz testcase resets the receive directory and restarts one `storescp` process. The target is not coverage-instrumented; AFLNet's helper bitmap is not pynetdicom source coverage.

Upstream: [pynetdicom releases](https://github.com/pydicom/pynetdicom/releases), [storescp documentation](https://pydicom.github.io/pynetdicom/stable/apps/storescp.html), [PyPI package and provenance](https://pypi.org/project/pynetdicom/3.0.4/).

After the formal run, replay the saved raw queue and run the post-campaign smoke plus listener shutdown check:

```sh
docker compose --env-file images.env -f compose.yaml run --rm --entrypoint python3 fuzz \
  /opt/benchmark/replay_queue.py \
  /results/pynetdicom-fuzz-30m-20261112/queue \
  /results/pynetdicom-fuzz-30m-20261112/replay-validation
./post-smoke.sh /results/dicom-smoke-post-20261112
```

Framework adaptation lessons are maintained in the central `基准化经验库.md`, not copied into this ZIP.
