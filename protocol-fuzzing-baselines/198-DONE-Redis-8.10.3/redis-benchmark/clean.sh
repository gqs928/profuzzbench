#!/usr/bin/env bash
# AFLNet's -K restarts redis-server for each testcase. Persistence is disabled,
# so restarting the process clears all volatile keys and client protocol state.
exit 0
