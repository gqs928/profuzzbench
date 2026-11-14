# Queue replay framing correction

The first post-campaign replay pass treated all queue files as raw SMTP bytes.
That assumption was wrong for 12 AFLNet `-E` outputs: the four-byte request
lengths are unsigned little-endian values preceding each request. The raw AFLNet
`queue/` contains 8 unframed byte streams; `replayable-queue/` and
`replayable-new-ipsm-paths/` contain 12 framed request sequences.

`replay.py` now decodes these two formats explicitly, then preserves the SMTP
`DATA` command/body transaction and its 354/final-reply handshake. The corrected
rerun passed all 20 inputs: 20/20 TCP connections and 220 greetings, 89 requests,
3/3 DATA transactions with 354 and final 250, 0 reply timeouts, 0 connection
errors, healthy Postfix master, and clean listener shutdown. The corrected
summary is `results/postfix-smtp-30m-20261113/queue-replay.json`; its dedicated
replay-phase coverage is in `replay-verified/`. The first misframed JSON is kept
as `queue-replay-initial-unframed-harness.json` only to make the correction
auditable; it is superseded and must not be used as acceptance evidence.

`build-logs/build-inputs.sha256` records the exact original image inputs. The
original `replay.py` was extracted from that image to
`build-logs/replay.py-as-built.py` and its hash matches the build manifest. The
corrected replay ran in a temporary network-isolated container using the same
built Postfix image and the updated host replay script; target source and
fuzzer binary were not changed. Rebuilding from this final package includes the
corrected decoder in the image.

The 1,800-second AFLNet campaign itself was not rerun or changed by this replay
fix; its timing, queue, state, stability, crash/hang, and target gcov evidence
remain unchanged.
