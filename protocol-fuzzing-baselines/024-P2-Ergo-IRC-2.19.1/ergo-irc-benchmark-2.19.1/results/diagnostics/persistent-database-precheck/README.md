# Superseded short campaign: persistent target database

This roughly 100-second run is not a formal result. The first target launcher reused the same `ircd.db` across AFLNet executions. Because Ergo stores account and channel state in that file, samples could affect later samples. The final launcher clears a separate target working directory before every execution; the fuzzer's own working directory remains intact.
