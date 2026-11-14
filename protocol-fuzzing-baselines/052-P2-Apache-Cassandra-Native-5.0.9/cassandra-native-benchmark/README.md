# Apache Cassandra 5.0.9 — Native Protocol benchmark

The target is the official Apache Cassandra image pinned to its linux/amd64 manifest digest. The tested scope is unauthenticated Cassandra Native Protocol v4 over TCP port 9042. One isolated Cassandra process remains alive during the campaign; the reset hook removes every non-system keyspace before each testcase. The data, commitlog, saved-cache, and hints directories are cleared when the process is initially started.

The Cassandra target binary is not coverage-instrumented. AFLNet uses a Cassandra frame/state adapter and retains new response-state paths; the AFL bitmap remains 0% and is not source coverage. Replay records raw TCP inputs separately from AFLNet's four-byte-length-prefixed KL-message queues. It follows the same per-sample keyspace reset as the formal campaign, so queue replay validates the campaign's logical reset boundary rather than using a fresh JVM for every sample.
