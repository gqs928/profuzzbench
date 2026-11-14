#!/usr/bin/env bash
# Memcached cache state is process-local. AFLNet's -K lifecycle discards its
# per-test server process; never kill unrelated host/system Memcached daemons.
exit 0
