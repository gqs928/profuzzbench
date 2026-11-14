# Dovecot POP3 benchmark (2.4.5)

This package builds the official stable Dovecot 2.4.5 release with its POP3 service enabled and benchmarks the plaintext POP3 command path with AFLNet. The Dovecot and AFLNet archives are SHA-256 pinned. The image contains reference, AFL-instrumented and gcov-instrumented builds compiled from the same Dovecot release source.

## Build and validate

On a Linux host with Docker and network access for the pinned Ubuntu snapshot and Dovecot Unicode data:

```sh
chmod +x ./*.sh
./build.sh dovecot-pop3-aflnet:2.4.5
./validate.sh dovecot-pop3-aflnet:2.4.5 "$PWD/results/pop3-validation" 60s
```

Validation runs five authenticated POP3 transactions against both the reference and AFL variants. Each transaction checks CAPA, invalid and valid credentials, STAT, LIST, UIDL, RETR, NOOP, DELE, RSET and QUIT. It then performs a short AFLNet run and verifies nonzero executions and a multi-state IPSM graph.

The upstream release archive contains a generated `configure` script but no `autogen.sh`; the build uses the shipped configure script and verifies each downloaded Unicode data file against `ucd-checksums.sha256`. The container also provides the `dovecot` system group required by the release's default service configuration. AFLNet targets an AFL-instrumented supervisor that starts one Dovecot master per testcase, forwards termination signals to its process group, and closes the inherited forkserver control descriptors before `exec`. This keeps one outer AFLNet forkserver while the actual POP3 workers inherit the coverage map and remain part of the supervised service lifecycle.

POP3 dictionary control bytes use AFL hexadecimal escapes (for example, `\x0d\x0a`). `validate.sh` rejects raw control bytes before starting Docker so line endings stay portable.

## Thirty-minute baseline

```sh
mkdir -p results
docker run --rm --network none --user root \
  -v "$PWD:/workspace:ro" -v "$PWD/results:/results" \
  dovecot-pop3-aflnet:2.4.5 \
  bash /workspace/run.sh /results/pop3-30m 30m
```

The service binds only to loopback TCP/1110 inside the isolated container. A fixed one-message Maildir is restored before each testcase so that POP3 operations on message 1 start from the same mailbox state. The AFLNet POP3 adapter treats each LF-terminated command as a request, maps `+OK` and `-ERR` to stable states, and emits a separate state at the dot terminator of positive multiline replies while ignoring message-body text.

The report covers protocol handling, AFLNet execution and protocol-state feedback. It does not claim throughput, TLS, external mail delivery or external authentication coverage, and it is not a security audit.

## Pinned sources

- Dovecot 2.4.5 official stable archive: [release index](https://dovecot.org/releases/2.4/), [release announcement](https://dovecot.org/mailman3/archives/list/dovecot%40dovecot.org/thread/D7FJQODYCY23BG3FWUZXCJRCLCPT7RZT/)
- POP3: [RFC 1939](https://www.rfc-editor.org/rfc/rfc1939)
- AFLNet snapshot: ProFuzzBench commit `0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732`
- Source archive locks: `source-lock.json`, `source-checksums.sha256`; Dovecot UCD data hashes: `ucd-checksums.sha256`
