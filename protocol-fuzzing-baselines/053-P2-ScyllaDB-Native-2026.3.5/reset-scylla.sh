#!/usr/bin/env bash
set -euo pipefail
WORKDIR=${WORKDIR:-/opt/benchmark}
LIFECYCLE_LOG=${SCYLLA_LIFECYCLE_LOG:-/results/scylla-lifecycle.tsv}
EXPECTED_CQL_RELEASE=${SCYLLA_CQL_RELEASE_VERSION:-3.0.8}
mkdir -p "$(dirname "$LIFECYCLE_LOG")"
record() { printf '%s\t%s\n' "$(date -u +%FT%TZ)" "$*" >> "$LIFECYCLE_LOG"; }
if ! /bin/bash "$WORKDIR/start-scylla.sh"; then record 'reset-failed=server-not-ready'; exit 1; fi
keyspaces=$(cqlsh 127.0.0.1 9042 --protocol-version=4 --request-timeout=10 -e 'SELECT keyspace_name FROM system_schema.keyspaces')
mapfile -t user_keyspaces < <(awk '
 /^[[:space:]]*keyspace_name[[:space:]]*$/ { next }
 /^-+$/ { in_rows = 1; next }
 in_rows && /^\([0-9]+ rows?\)$/ { exit }
 in_rows { gsub(/^[[:space:]]+|[[:space:]]+$/, ""); if (length($0)) print $0 }
' <<< "$keyspaces")
dropped=0
for keyspace in "${user_keyspaces[@]}"; do
 case "$keyspace" in system|system_auth|system_distributed|system_schema|system_traces|system_views|system_virtual_schema) continue;; esac
 [[ "$keyspace" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] || { record 'reset-failed=invalid-keyspace-name'; exit 1; }
 cqlsh 127.0.0.1 9042 --protocol-version=4 --request-timeout=10 -e "DROP KEYSPACE IF EXISTS \"${keyspace}\"" >/dev/null
 dropped=$((dropped + 1))
done
record "reset-ok product_version=${SCYLLA_EXPECTED_VERSION:-2026.3.5} cql_release_version=$EXPECTED_CQL_RELEASE user_keyspaces_dropped=$dropped"
