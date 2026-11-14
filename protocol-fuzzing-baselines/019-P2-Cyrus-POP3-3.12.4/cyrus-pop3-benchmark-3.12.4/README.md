# Cyrus POP3 benchmark (3.12.4)

This package builds the official Cyrus IMAP server 3.12.4 release with the POP3 service enabled and benchmarks the plaintext POP3 authorization and mailbox command path using AFLNet. The Cyrus and AFLNet source archives are SHA-256 pinned. Reference, AFL/ASan and gcov server builds use the same Cyrus source and configuration.

## Build and validate

On a Linux host with Docker:

```sh
chmod +x ./*.sh
./build.sh cyrus-pop3-aflnet:3.12.4
./validate.sh cyrus-pop3-aflnet:3.12.4 "$PWD/results/pop3-validation" 60s
```

Validation repeats authenticated POP3 sessions against the reference and AFL builds. It checks CAPA, invalid and valid USER/PASS, STAT, LIST, UIDL, RETR, NOOP, DELE, RSET and QUIT. It then runs AFLNet and verifies nonzero executions plus a multi-state IPSM graph.

POP3 dictionary control bytes use AFL hexadecimal escapes (for example, `\x0d\x0a`). `validate.sh` rejects raw control bytes before starting Docker so line endings stay portable.

## Thirty-minute baseline

```sh
mkdir -p results
docker run --rm --hostname localhost --network none \
  -v "$PWD:/workspace:ro" -v "$PWD/results:/results" \
  cyrus-pop3-aflnet:3.12.4 \
  bash /workspace/run.sh /results/pop3-30m 30m
```

The image creates a fixed one-message Cyrus mailbox snapshot once using the reference build. The target launcher restores that snapshot before starting POP3 for each testcase. This makes `RETR 1`, `DELE 1` and `RSET` replay from the same initial mailbox state. POP3 listens only on isolated loopback TCP/1110. The target also runs the Cyrus SASL helper; the runner starts it outside the AFL-instrumented server path and keeps AFLNet's forkserver descriptors on the instrumented Cyrus master.

The parser splits one line-framed POP3 command per request region, preserves a partial final command, maps `+OK`/`-ERR` responses to stable IDs and recognizes positive multiline dot termination while ignoring message body text. The result measures server execution and state feedback; it is not a throughput benchmark or security audit and does not cover TLS or external authentication/mailbox backends.

## Upstream references

- Cyrus IMAP 3.12.4: [official release notes](https://www.cyrusimap.org/3.12/imap/download/release-notes/3.12/x/3.12.4.html), [release archive](https://github.com/cyrusimap/cyrus-imapd/releases)
- POP3: [RFC 1939](https://www.rfc-editor.org/rfc/rfc1939)
- AFLNet snapshot: ProFuzzBench commit `0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732`
- Archive hashes: `source-checksums.sha256`; deterministic corpus: `seeds-manifest.json`
