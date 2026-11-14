# Seed compatibility finding

The original TinyDTLS client captures were structurally valid DTLS 1.2 records, but GnuTLS 3.8.13 rejected their first ClientHello with `The certificate type is not supported.` AFLNet therefore received no DTLS response state during its dry run and refused to start state-aware fuzzing.

The replacement seeds are first-flight ClientHello datagrams captured from three successful GnuTLS 3.8.13 `gnutls-cli` handshakes through the local UDP relay in `capture_seeds.py`. Distinct SNI values make the three seeds non-identical. The matching client/server smoke test completed all three handshakes, and AFLNet's replay parser decoded the server response states as `0-5634-5643-5644-5645-5646-`.

The rejected reference inputs are preserved under `tinydtls-reference/` for reproducibility; they are excluded from the AFLNet input directory.
