#!/usr/bin/env bash
# AFLNet calls -c after starting the target and immediately before connecting.
# The launcher resets server state before exec; this hook must leave it running.
exit 0
