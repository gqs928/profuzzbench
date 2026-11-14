# Aborted preflight attempt 1

The three target-specific QUIC Initial smoke passes succeeded: each 1,200-byte Initial produced a 51-byte Initial response; the server remained alive after input, exited on controlled SIGTERM, and released UDP/4433.

AFLNet then exited immediately with status 127 because the runtime image lacked `libcgraph.so.8`. No fuzz campaign started and no queue was produced. This attempt is retained for framework diagnostics. The next image revision installs `libcgraph8` and verifies runtime dependencies for both AFLNet and picoquicdemo before repeating preflight.
