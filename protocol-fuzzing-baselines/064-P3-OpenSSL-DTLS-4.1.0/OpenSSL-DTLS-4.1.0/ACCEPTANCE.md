# OpenSSL DTLS 1.2 baseline acceptance

Status: complete.

Acceptance requires all of the following:

- Official OpenSSL 4.1.0 source checksum and detached signature verified against the official OpenSSL release signing keyring.
- Runtime version check reports OpenSSL 4.1.0, the custom echo harness links the instrumented libssl/libcrypto, and AFLNet contains the DTLS12 parser.
- Three consecutive DTLS 1.2 handshakes and reverse-echo probes succeed against the instrumented custom target.
- AFLNet completes its seed dry run and the bounded campaign reaches the supervisor's 1,800-second deadline. Final AFLNet stats span 1,801 seconds because the last stats write follows the deadline signal by about one second: 18,804 executions, 314 paths, 104 variable paths, 95.27% stability, 25.46% instrumented bitmap, 27 cycles, and zero crashes or hangs. The bitmap reflects the instrumented echo harness/OpenSSL libraries, not source-level OpenSSL coverage.
- The complete 636-sample raw/KL/IPSM queue replay is accounted for: 418 structurally valid samples reached target readiness, 218 malformed DTLS record streams were rejected by the replay framing validator before send, and 404 response datagrams with 1,167 response states were parsed. Of the valid samples, 284 left the one-client target alive and 134 ended with the target's expected clean exit (return code 0) on malformed or incomplete handshakes; there were no nonzero target exits or replay transport errors.
- Post-run smoke checks pass and no OpenSSL process or UDP listener remains.
- The standalone ZIP passes CRC and SHA-256 validation and excludes the shared experience library. The exact protocol image is removed after packaging.

The formal stats, exact deadline JSON, pre/post handshake-and-reverse-echo evidence, listener check, full replay JSON/logs, runtime logs, image identity, and SHA-256 package checksum are included in the standalone delivery. The shared automation-framework experience remains in the central deliverables folder.
