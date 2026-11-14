# Preflight attempt 1 diagnostic note

The three target-specific QUIC Initial smoke passes succeeded, each returning a 107-byte Retry and releasing UDP/4433 after controlled SIGTERM. AFLNet then exited immediately with status 127 because the runtime image lacked libcgraph.so.8. A read-only ldd check confirmed this was the only missing shared library; libcgraph8 has been added to the runtime package list. No formal campaign was started. The second preflight will use a fresh result directory.
