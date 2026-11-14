#!/usr/bin/env bash
# The benchmark config disables persistence; AFLNet -K restarts the broker
# process between test cases, which resets all volatile MQTT sessions.
exit 0
