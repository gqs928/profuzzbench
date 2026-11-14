# Failed diagnostic attempt: AFLNet black-box helper lifecycle

This run is intentionally not accepted as a preflight. AFLNet was invoked with `-n -K -- /bin/sleep 3600` while MediaMTX ran independently. AFLNet's network cleanup path sent SIGTERM to the child and then spun until `kill(pid, 0)` failed; the child became a zombie, so that loop could not finish and the fuzzer ignored the campaign timer. The mounted log, Go `covmeta`, start marker, and fuzzer outputs are retained as diagnostic evidence. No formal coverage or campaign result is claimed for this attempt.
