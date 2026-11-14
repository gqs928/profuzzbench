# Preflight validation

- Date: 2026-11-09
- STOMP 1.2 CONNECTED, queue SUBSCRIBE receipt, and SEND delivery smoke: PASS.
- AFLNet preflight: requested 25 active seconds; recorded 27 seconds, 118 executions, 9 paths, 100.00% stability, 0 crash, 0 hang.
- The initial-corpus dry run completed after the target helper was changed to exit after ensuring the independent broker is ready. `-D` is 10,000 microseconds (10 ms), `-W` is 100 ms, and `-w` is 200,000 microseconds (200 ms).
- An un-terminated STOMP tail remains a parser unit-test fixture, not a live fuzz seed: the broker correctly waits for NUL frame termination. The malformed-command seed includes a receipt so the broker returns an ERROR response.
